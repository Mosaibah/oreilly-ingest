import html as html_lib
import re

from .base import Plugin
from core.types import ChapterInfo
import config


def _format_mmss(timestamp_str: str) -> str:
    """Convert '00:01:23.456' to '01:23' (or '01:02:03' if >= 1 hour)."""
    if not timestamp_str:
        return "00:00"
    main_part = timestamp_str.split(".")[0]
    parts = main_part.split(":")
    if len(parts) == 3:
        h, m, s = parts
        if h == "00":
            return f"{m}:{s}"
        return f"{h}:{m}:{s}"
    return main_part


def _parse_seconds(timestamp_str: str) -> float:
    """Convert 'HH:MM:SS.mmm' into float seconds."""
    if not timestamp_str:
        return 0.0
    try:
        parts = timestamp_str.split(":")
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        return float(parts[0])
    except Exception:
        return 0.0


class ChaptersPlugin(Plugin):
    """Plugin for fetching book chapters or video course lessons and their content."""

    def __init__(self):
        super().__init__()
        self._clip_cache: dict[str, dict] = {}
        self._clip_titles: dict[str, str] = {}

    def fetch_list(self, book_id: str) -> list[ChapterInfo]:
        """Fetch list of chapters for a book or video course."""
        url = f"{config.API_V2}/epub-chapters/?epub_identifier=urn:orm:book:{book_id}"
        chapters: list[ChapterInfo] = []

        try:
            while url:
                data = self.http.get_json(url)
                for ch in data.get("results", []):
                    chapters.append(ChapterInfo(
                        ourn=ch.get("ourn", ""),
                        title=ch.get("title", ""),
                        filename=self._extract_filename(ch.get("reference_id", "")),
                        content_url=ch.get("content_url", ""),
                        images=(ch.get("related_assets") or {}).get("images", []),
                        stylesheets=(ch.get("related_assets") or {}).get("stylesheets", []),
                        virtual_pages=ch.get("virtual_pages"),
                        minutes_required=ch.get("minutes_required"),
                    ))
                url = data.get("next")
        except Exception:
            chapters = []

        if not chapters:
            return self._fetch_video_chapters(book_id)

        return chapters

    def _fetch_video_chapters(self, book_id: str) -> list[ChapterInfo]:
        """Fetch hierarchical video lessons and syllabus for a video course."""
        chapters: list[ChapterInfo] = []

        # Prepend a synthetic syllabus & exercises overview chapter
        chapters.append(
            ChapterInfo(
                ourn=f"urn:orm:video:{book_id}:syllabus",
                title="00. Course Syllabus, Learning Objectives & Exercises",
                filename="000_course_syllabus_and_exercises.html",
                content_url=f"video-syllabus://{book_id}",
                images=[],
                stylesheets=[],
                virtual_pages=None,
                minutes_required=1.0,
            )
        )

        toc_items = []
        try:
            toc_data = self.http.get_json(f"{config.API_V1}/videotocs/{book_id}/")
            toc_items = toc_data.get("toc", []) if isinstance(toc_data, dict) else []
        except Exception:
            toc_items = []

        if toc_items:
            current_module = ""
            clip_idx = 1
            for item in toc_items:
                depth = item.get("depth", 2)
                ourn = item.get("ourn")
                duration = item.get("duration")
                title = (item.get("title") or "").strip()
                ref_id = item.get("reference_id") or ""

                # Depth 1 without clip ourn is a Module / Chapter header
                if depth == 1 and not ourn and duration is None:
                    current_module = title
                    continue

                if not ref_id:
                    continue

                linkid = item.get("linkid") or self._extract_filename(ref_id)
                safe_slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:48] or linkid
                display_title = f"{current_module} — {title}" if current_module else title
                self._clip_titles[ref_id] = display_title
                minutes = round(float(duration) / 60.0, 1) if duration else None

                chapters.append(
                    ChapterInfo(
                        ourn=ourn or f"urn:orm:video:{book_id}:video-clip:{linkid}",
                        title=display_title,
                        filename=f"{clip_idx:03d}_{linkid}_{safe_slug}.html",
                        content_url=f"{config.API_V1}/videoclips/{ref_id}/",
                        images=[],
                        stylesheets=[],
                        virtual_pages=None,
                        minutes_required=minutes,
                    )
                )
                clip_idx += 1
            return chapters

        # Fallback to videoplaylists if videotocs was empty
        playlist = self.http.get_json(f"{config.API_V1}/videoplaylists/{book_id}/")
        for idx, clip_url in enumerate(playlist.get("video_clips", []), start=1):
            ref_id = clip_url.rstrip("/").split("/")[-1]
            chapters.append(
                ChapterInfo(
                    ourn=f"urn:orm:video:{book_id}:video-clip:{ref_id}",
                    title=f"Lesson {idx}: {ref_id}",
                    filename=f"{idx:03d}_{ref_id}.html",
                    content_url=clip_url if clip_url.startswith("http") else f"{config.BASE_URL}{clip_url}",
                    images=[],
                    stylesheets=[],
                    virtual_pages=None,
                    minutes_required=None,
                )
            )
        return chapters

    def fetch_toc(self, book_id: str) -> list[dict]:
        url = f"{config.API_V2}/epubs/urn:orm:book:{book_id}/table-of-contents/"
        try:
            data = self.http.get_json(url)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return data.get("results", [])
        except Exception:
            # Video courses do not use the /api/v2/epubs/ TOC endpoint
            return []
        return []

    _FRONT_MATTER_KEYWORDS = ("cover", "halftitle", "titlepage", "title-page", "contents", "toc")

    def reorder_by_toc(self, chapters: list[ChapterInfo], toc: list[dict]) -> list[ChapterInfo]:
        """Reorder chapters to match the TOC reading order."""
        ordered_filenames = self._flatten_toc_filenames(toc)
        if not ordered_filenames:
            return chapters

        chapter_map = {ch["filename"]: ch for ch in chapters}

        ordered = []
        for filename in ordered_filenames:
            if filename in chapter_map:
                ordered.append(chapter_map.pop(filename))

        # Split remaining into front matter (before TOC content) and back matter (after)
        front = []
        back = []
        for ch in chapters:
            if ch["filename"] not in chapter_map:
                continue
            if self._is_front_matter(ch):
                front.append(ch)
            else:
                back.append(ch)

        return front + ordered + back

    def _is_front_matter(self, ch: ChapterInfo) -> bool:
        filename_lower = ch["filename"].lower()
        title_lower = ch["title"].lower()
        for keyword in self._FRONT_MATTER_KEYWORDS:
            if keyword in filename_lower or keyword in title_lower:
                return True
        return False

    def fetch_content(self, content_url: str) -> str:
        if content_url.startswith("video-syllabus://"):
            book_id = content_url.split("video-syllabus://", 1)[1].strip("/")
            return self._render_video_syllabus_html(book_id)
        if "/api/v1/videoclips/" in content_url:
            return self._render_video_clip_html(content_url)
        return self.http.get_text(content_url)

    def fetch_video_clip_data(self, content_url: str) -> dict:
        """Fetch and cache raw JSON metadata and transcriptions for a video clip."""
        if content_url in self._clip_cache:
            return self._clip_cache[content_url]
        data = self.http.get_json(content_url)
        self._clip_cache[content_url] = data
        return data

    def _render_video_syllabus_html(self, book_id: str) -> str:
        """Render a comprehensive course syllabus, objectives, and exercises page as HTML."""
        book_plugin = self.kernel["book"] if self.kernel else None
        course_info = book_plugin.fetch(book_id) if book_plugin else {"title": book_id}

        title = html_lib.escape(course_info.get("title") or book_id)
        authors = html_lib.escape(", ".join(course_info.get("authors") or []))
        publishers = html_lib.escape(", ".join(course_info.get("publishers") or []))
        pub_date = html_lib.escape(str(course_info.get("publication_date") or ""))
        duration_secs = course_info.get("duration_seconds") or 0
        duration_hours = f"{duration_secs // 3600}h {(duration_secs % 3600) // 60}m" if duration_secs else "N/A"
        description_html = course_info.get("description") or ""

        parts = [
            '<div id="sbo-rt-content">',
            f"<h1>{title} — Course Syllabus &amp; Study Guide</h1>",
            "<ul>",
            f"<li><strong>Content Type:</strong> Video Course</li>",
            f"<li><strong>Course ID / ISBN:</strong> {html_lib.escape(book_id)}</li>",
        ]
        if authors:
            parts.append(f"<li><strong>Instructors / Authors:</strong> {authors}</li>")
        if publishers:
            parts.append(f"<li><strong>Publisher:</strong> {publishers}</li>")
        if pub_date:
            parts.append(f"<li><strong>Publication Date:</strong> {pub_date}</li>")
        parts.append(f"<li><strong>Total Running Time:</strong> {duration_hours} ({duration_secs} seconds)</li>")
        parts.append("</ul>")

        if description_html:
            parts.append("<h2>Course Overview &amp; Learning Objectives</h2>")
            parts.append(f"<div>{description_html}</div>")

        resources = course_info.get("resources") or []
        if resources:
            parts.append("<h2>Exercises, Code Repositories &amp; Supplemental Files</h2>")
            parts.append("<ul>")
            for res in resources:
                r_url = html_lib.escape(res.get("url") or "")
                r_desc = html_lib.escape(res.get("description") or res.get("type") or "Course Exercise Resource")
                if r_url:
                    parts.append(f'<li><strong>{r_desc}:</strong> <a href="{r_url}">{r_url}</a></li>')
            parts.append("</ul>")

        # Syllabus Breakdown from videotocs
        try:
            toc_data = self.http.get_json(f"{config.API_V1}/videotocs/{book_id}/")
            toc_items = toc_data.get("toc", []) if isinstance(toc_data, dict) else []
        except Exception:
            toc_items = []

        if toc_items:
            parts.append("<h2>Complete Course Syllabus (Modules, Video Lessons &amp; Hands-On Demos)</h2>")
            in_list = False
            for item in toc_items:
                depth = item.get("depth", 2)
                ourn = item.get("ourn")
                duration = item.get("duration")
                item_title = html_lib.escape((item.get("title") or "").strip())
                ref_id = html_lib.escape(item.get("reference_id") or "")

                if depth == 1 and not ourn and duration is None:
                    if in_list:
                        parts.append("</ul>")
                        in_list = False
                    parts.append(f"<h3>{item_title}</h3>")
                else:
                    if not in_list:
                        parts.append("<ul>")
                        in_list = True
                    mins = f"{round(float(duration) / 60.0, 1)} min" if duration else "video"
                    lower_t = item_title.lower()
                    is_exercise = any(
                        kw in lower_t
                        for kw in ("demo", "lab", "exercise", "hands-on", "solution", "practice", "coding", "walkthrough")
                    )
                    badge = " <strong>[HANDS-ON DEMO / EXERCISE]</strong>" if is_exercise else ""
                    parts.append(f"<li><code>{ref_id}</code> — <strong>{item_title}</strong> ({mins}){badge}</li>")
            if in_list:
                parts.append("</ul>")

        quizzes = course_info.get("quizzes") or []
        if quizzes:
            parts.append("<h2>Practice Quizzes &amp; Assessments</h2>")
            parts.append("<ul>")
            for q in quizzes:
                q_name = html_lib.escape(q.get("name") or "Quiz")
                q_type = html_lib.escape(q.get("quiz_type") or "assessment")
                sec_ourn = html_lib.escape(q.get("section_ourn") or "")
                threshold = q.get("passing_score_threshold")
                parts.append(
                    f"<li><strong>{q_name}</strong> (Type: {q_type}, Passing Score: {threshold}%, Attached to: <code>{sec_ourn}</code>)</li>"
                )
            parts.append("</ul>")

        parts.append("</div>")
        return "\n".join(parts)

    def _render_video_clip_html(self, content_url: str) -> str:
        """Fetch a video clip JSON and convert its metadata + timestamped transcript into semantic HTML."""
        clip = self.fetch_video_clip_data(content_url)
        raw_ref_id = clip.get("reference_id") or ""
        full_title = self._clip_titles.get(raw_ref_id) or clip.get("title") or "Video Lesson"
        title = html_lib.escape(full_title)
        ref_id = html_lib.escape(raw_ref_id)
        duration = clip.get("duration") or 0
        mins = round(float(duration) / 60.0, 1) if duration else 0
        description = (clip.get("description") or "").strip()

        lower_meta = f"{title} {description}".lower()
        is_exercise = any(
            kw in lower_meta
            for kw in ("demo", "lab", "exercise", "hands-on", "solution", "practice", "walkthrough")
        )
        lesson_type = "Hands-On Demo / Exercise Video" if is_exercise else "Video Lecture"

        parts = [
            '<div id="sbo-rt-content">',
            f"<h1>{title}</h1>",
            "<ul>",
            f"<li><strong>Lesson Type:</strong> {lesson_type}</li>",
            f"<li><strong>Clip Reference ID:</strong> <code>{ref_id}</code></li>",
            f"<li><strong>Duration:</strong> {mins} minutes ({duration} seconds)</li>",
            "</ul>",
        ]

        if description:
            parts.append("<h2>Lesson Summary &amp; Objectives</h2>")
            parts.append(f"<p>{html_lib.escape(description)}</p>")

        paragraphs = self._consolidate_transcript_lines(clip)
        if paragraphs:
            parts.append("<h2>Video Transcript (Timestamped)</h2>")
            for start_ts, end_ts, text_block in paragraphs:
                escaped_text = html_lib.escape(text_block)
                parts.append(f"<p><strong>[{start_ts} - {end_ts}]</strong> {escaped_text}</p>")
        else:
            parts.append("<p><em>No transcript available for this video clip.</em></p>")

        parts.append("</div>")
        return "\n".join(parts)

    def _consolidate_transcript_lines(
        self,
        clip_data: dict,
        window_seconds: float = 60.0,
        max_chars: int = 550,
    ) -> list[tuple[str, str, str]]:
        """Group granular caption lines into coherent, sentence-aligned paragraphs with [MM:SS] timestamps."""
        transcriptions = clip_data.get("transcriptions") or []
        if not transcriptions:
            return []

        lines = (transcriptions[0].get("transcription") or {}).get("lines") or []
        if not lines:
            return []

        paragraphs: list[tuple[str, str, str]] = []
        buf_texts: list[str] = []
        block_start_str = ""
        block_end_str = ""
        block_start_sec = 0.0
        char_count = 0

        for line in lines:
            text = (line.get("text") or "").strip()
            if not text:
                continue
            begin_str = line.get("begin") or "00:00:00.000"
            end_str = line.get("end") or begin_str
            begin_sec = _parse_seconds(begin_str)

            if not buf_texts:
                block_start_str = _format_mmss(begin_str)
                block_start_sec = begin_sec

            buf_texts.append(text)
            block_end_str = _format_mmss(end_str)
            char_count += len(text) + 1

            elapsed = begin_sec - block_start_sec
            ends_sentence = text.endswith((".", "?", "!"))
            if (elapsed >= window_seconds and ends_sentence) or char_count >= max_chars:
                paragraphs.append((block_start_str, block_end_str, " ".join(buf_texts)))
                buf_texts = []
                char_count = 0

        if buf_texts:
            paragraphs.append((block_start_str, block_end_str, " ".join(buf_texts)))

        return paragraphs

    def format_webvtt(self, clip_data: dict) -> str:
        """Export clip transcription lines as a standard WebVTT (.vtt) subtitle file."""
        transcriptions = clip_data.get("transcriptions") or []
        if not transcriptions:
            return ""
        lines = (transcriptions[0].get("transcription") or {}).get("lines") or []
        if not lines:
            return ""

        vtt = ["WEBVTT", ""]
        for idx, line in enumerate(lines, start=1):
            text = (line.get("text") or "").strip()
            if not text:
                continue
            begin = line.get("begin") or "00:00:00.000"
            end = line.get("end") or begin
            vtt.append(str(idx))
            vtt.append(f"{begin} --> {end}")
            vtt.append(text)
            vtt.append("")
        return "\n".join(vtt)

    def get_kaltura_mp4_url(self, reference_id: str, kaltura_entry_id: str) -> str | None:
        """Resolve an authenticated Kaltura direct MP4 download URL for a video clip."""
        if not reference_id or not kaltura_entry_id:
            return None
        ks_url = f"{config.API_V1}/player/kaltura_session/?reference_id={reference_id}"
        ks_data = self.http.get_json(ks_url)
        ks = ks_data.get("session")
        if not ks:
            return None
        return (
            f"https://cdnapisec.kaltura.com/p/1926081/sp/192608100/playManifest/"
            f"entryId/{kaltura_entry_id}/format/url/protocol/https/ks/{ks}/video.mp4"
        )

    def _extract_filename(self, reference_id: str) -> str:
        if "-/" in reference_id:
            return reference_id.split("-/")[1]
        return reference_id

    def _flatten_toc_filenames(self, toc_items: list[dict]) -> list[str]:
        """Extract ordered, deduplicated filenames from the TOC tree."""
        result: list[str] = []
        seen: set[str] = set()

        def walk(items: list[dict]):
            for item in items:
                ref_id = item.get("reference_id", "")
                if ref_id:
                    filename = self._extract_filename(ref_id)
                    if filename and filename not in seen:
                        result.append(filename)
                        seen.add(filename)
                children = item.get("children", [])
                if children:
                    walk(children)

        walk(toc_items)
        return result

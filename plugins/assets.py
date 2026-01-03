from pathlib import Path
from typing import Callable

from .base import Plugin


class AssetsPlugin(Plugin):
    def download_image(self, url: str, save_path: Path) -> bool:
        if save_path.exists():
            return True

        save_path.parent.mkdir(parents=True, exist_ok=True)
        content = self.http.get_bytes(url)
        save_path.write_bytes(content)
        return True

    def download_css(self, url: str, save_path: Path) -> bool:
        if save_path.exists():
            return True

        save_path.parent.mkdir(parents=True, exist_ok=True)
        content = self.http.get_text(url)
        save_path.write_text(content)
        return True

    def download_all_images(
        self,
        urls: list[str],
        output_dir: Path,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, Path]:
        downloaded = {}
        total = len(urls)
        for i, url in enumerate(urls):
            filename = url.split("/")[-1]
            save_path = output_dir / "Images" / filename
            self.download_image(url, save_path)
            downloaded[url] = save_path
            if progress_callback:
                progress_callback(i + 1, total)
        return downloaded

    def download_all_css(
        self,
        urls: list[str],
        output_dir: Path,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, Path]:
        downloaded = {}
        total = len(urls)
        for i, url in enumerate(urls):
            save_path = output_dir / "Styles" / f"Style{i:02d}.css"
            self.download_css(url, save_path)
            downloaded[url] = save_path
            if progress_callback:
                progress_callback(i + 1, total)
        return downloaded

    def get_cover_url(self, book_id: str) -> str:
        return f"https://learning.oreilly.com/library/cover/{book_id}/"

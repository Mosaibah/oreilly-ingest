from .http_client import HttpClient


class Kernel:
    def __init__(self, http: HttpClient | None = None):
        self.http = http or HttpClient()
        self._plugins: dict[str, object] = {}

    def register(self, name: str, plugin):
        plugin.kernel = self
        self._plugins[name] = plugin

    def get(self, name: str):
        return self._plugins.get(name)

    def __getitem__(self, name: str):
        return self._plugins[name]


def create_default_kernel() -> Kernel:
    """Create a kernel with all standard plugins registered."""
    from plugins import (
        AuthPlugin,
        BookPlugin,
        ChaptersPlugin,
        AssetsPlugin,
        HtmlProcessorPlugin,
        EpubPlugin,
        MarkdownPlugin,
        PdfPlugin,
        TokenPlugin,
        PlainTextPlugin,
        JsonExportPlugin,
        ChunkingPlugin,
        OutputPlugin,
        SystemPlugin,
        DownloaderPlugin,
    )

    kernel = Kernel()

    # Core plugins
    kernel.register("auth", AuthPlugin())
    kernel.register("book", BookPlugin())
    kernel.register("chapters", ChaptersPlugin())
    kernel.register("assets", AssetsPlugin())
    kernel.register("html_processor", HtmlProcessorPlugin())

    # Output format plugins
    kernel.register("epub", EpubPlugin())
    kernel.register("markdown", MarkdownPlugin())
    kernel.register("pdf", PdfPlugin())
    kernel.register("plaintext", PlainTextPlugin())
    kernel.register("json_export", JsonExportPlugin())
    kernel.register("chunking", ChunkingPlugin())
    kernel.register("token", TokenPlugin())

    # Orchestration & system plugins
    kernel.register("output", OutputPlugin())
    kernel.register("system", SystemPlugin())
    kernel.register("downloader", DownloaderPlugin())

    return kernel

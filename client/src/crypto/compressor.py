"""Zstandard compression/decompression wrapper."""
import zstandard as zstd
import logging

logger = logging.getLogger(__name__)

DEFAULT_COMPRESSION_LEVEL = 3  # Balanced speed/ratio


class Compressor:
    def __init__(self, level: int = DEFAULT_COMPRESSION_LEVEL):
        self.cctx = zstd.ZstdCompressor(level=level)
        self.dctx = zstd.ZstdDecompressor()

    def compress_chunk(self, data: bytes) -> bytes:
        return self.cctx.compress(data)

    def decompress_chunk(self, data: bytes) -> bytes:
        return self.dctx.decompress(data)

    def compress_file(self, source_path: str, dest_path: str, chunk_size: int = 100 * 1024 * 1024) -> int:
        """Compress file, return compressed size."""
        compressed_size = 0
        with open(source_path, "rb") as src, open(dest_path, "wb") as dst:
            compressor = self.cctx.stream_writer(dst)
            while True:
                chunk = src.read(chunk_size)
                if not chunk:
                    break
                compressor.write(chunk)
            compressor.flush(zstd.FLUSH_FRAME)
            compressed_size = dst.tell()
        return compressed_size

    def decompress_file(self, source_path: str, dest_path: str, chunk_size: int = 100 * 1024 * 1024) -> int:
        """Decompress file, return original size."""
        original_size = 0
        with open(source_path, "rb") as src, open(dest_path, "wb") as dst:
            decompressor = self.dctx.stream_reader(src)
            while True:
                chunk = decompressor.read(chunk_size)
                if not chunk:
                    break
                dst.write(chunk)
                original_size += len(chunk)
        return original_size

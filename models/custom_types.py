from typing import Any, Optional

from PIL import UnidentifiedImageError
from fastapi_storages import StorageImage
from fastapi_storages.exceptions import ValidationException
from fastapi_storages.integrations.sqlalchemy import ImageType
from sqlalchemy import Dialect

from utils.image_compress import compress_upload_file


class CustomImageType(ImageType):
    """Rasm yuklashda avtomatik siqish va o'lchamni cheklash."""

    def save(self, value: Any) -> str:
        value.file.seek(0)
        try:
            compressed, out_filename, width, height = compress_upload_file(
                value.file,
                value.filename or "image.jpg",
            )
        except UnidentifiedImageError:
            raise ValidationException("Invalid image file")

        image = StorageImage(
            name=self._get_path(out_filename),
            storage=self.storage,
            height=height,
            width=width,
        )
        image.write(file=compressed)
        compressed.close()
        value.file.close()
        return image.name

    def process_result_value(
        self, value: Any, dialect: Dialect
    ) -> Optional[StorageImage]:
        return super().process_result_value(value, dialect)

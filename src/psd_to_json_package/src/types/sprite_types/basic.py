import os
from PIL import Image
from ..sprite import Sprite
from ...helpers.optimize_pngs import optimize_pngs

class BasicSprite(Sprite):
    def process(self):
        if self.layer.is_group():
            return self.process_group()
        else:
            return self.process_single_layer()

    def process_group(self):
        result = {
            **self.layer_info,
            "width": self.layer.width,
            "height": self.layer.height
        }

        # Export mask if present
        self.export_mask(result)

        # Skip image processing in metadata-only mode
        if self.config.get('metadataOnly', False):
            return result

        merged_image = Image.new('RGBA', (self.layer.width, self.layer.height), (0, 0, 0, 0))

        for child_layer in self.layer:
            if child_layer.is_visible():
                child_image = child_layer.composite()
                merged_image.paste(child_image, (child_layer.left - self.layer.left, child_layer.top - self.layer.top), child_image)

        filename = f"{self.layer_info['name']}.png"
        file_path = self.export_image(merged_image, filename)

        self.optimize_image(file_path)

        result["filePath"] = file_path
        return result

    def process_single_layer(self):
        result = {
            **self.layer_info,
            "width": self.layer.width,
            "height": self.layer.height
        }

        # Export mask if present
        self.export_mask(result)

        # Skip image processing in metadata-only mode
        if self.config.get('metadataOnly', False):
            return result

        image = self.layer.composite()
        filename = f"{self.layer_info['name']}.png"
        file_path = self.export_image(image, filename)

        self.optimize_image(file_path)

        result["filePath"] = file_path
        return result

    def optimize_image(self, file_path):
        optimize_config = self.config.get('optimizePNGs', {})
        optimize_pngs(file_path, optimize_config)
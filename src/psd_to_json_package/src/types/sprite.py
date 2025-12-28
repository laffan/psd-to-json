import os
from PIL import Image
from psd_tools import PSDImage
from ..helpers.optimize_pngs import optimize_pngs

class Sprite:
    def __init__(self, layer_info, layer, config, output_dir, psd_name):
        self.layer_info = layer_info
        self.layer = layer
        self.config = config
        self.psd_name = psd_name
        self.output_dir = os.path.join(output_dir, psd_name)
        self.sprite_output_dir = os.path.join(self.output_dir, 'sprites')
        os.makedirs(self.sprite_output_dir, exist_ok=True)

    def process(self):
        """
        Process the sprite. This method should be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement process method")

    def export_image(self, image, filename):
        """
        Export the image to a file.
        """
        filepath = os.path.join(self.sprite_output_dir, filename)
        image.save(filepath, 'PNG')
        return os.path.relpath(filepath, self.output_dir)

    def has_mask(self):
        """
        Check if the layer has a mask.
        """
        return self.layer.mask is not None

    def export_mask(self, result):
        """
        Export the layer mask if it exists. Modifies result dict in place.
        Returns the result dict.
        """
        if not self.has_mask():
            return result

        result['mask'] = True

        # Add mask position from the mask's bounding box
        mask_bbox = self.layer.mask.bbox
        result['maskX'] = mask_bbox[0]
        result['maskY'] = mask_bbox[1]
        result['maskWidth'] = mask_bbox[2] - mask_bbox[0]
        result['maskHeight'] = mask_bbox[3] - mask_bbox[1]

        # Skip actual mask export in metadata-only mode
        if self.config.get('metadataOnly', False):
            return result

        mask_image = self.layer.mask.topil()
        mask_filename = f"{self.layer_info['name']}_mask.png"
        mask_filepath = os.path.join(self.sprite_output_dir, mask_filename)
        mask_image.save(mask_filepath, 'PNG')

        # Optimize the mask image
        optimize_pngs(mask_filepath, self.config.get('pngQualityRange', {}))

        result['maskPath'] = os.path.relpath(mask_filepath, self.output_dir)
        return result

    @staticmethod
    def create_sprite(layer_info, layer, config, output_dir, psd_name):
        """
        Factory method to create the appropriate sprite subclass.
        """
        from .sprite_types.basic import BasicSprite
        from .sprite_types.spritesheet import SpritesheetSprite
        from .sprite_types.animation import AnimationSprite
        from .sprite_types.atlas import AtlasSprite

        sprite_type = layer_info.get('type', 'basic')
        
        if sprite_type == 'spritesheet':
            return SpritesheetSprite(layer_info, layer, config, output_dir, psd_name)
        elif sprite_type == 'animation':
            return AnimationSprite(layer_info, layer, config, output_dir, psd_name)
        elif sprite_type == 'atlas':
            return AtlasSprite(layer_info, layer, config, output_dir, psd_name)
        else:
            return BasicSprite(layer_info, layer, config, output_dir, psd_name)

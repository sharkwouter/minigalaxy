# Backward compatibility shim - this module is deprecated
# Use minigalaxy.compatibility_layer instead
from minigalaxy.compatibility_layer import CompatibilityLayer as Translator
from minigalaxy.compatibility_layer import CompatibilityLayerType as TranslatorType

__all__ = ['Translator', 'TranslatorType']

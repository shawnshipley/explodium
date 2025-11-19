bl_info = {
    "name": "Explodium",
    "description": "Shows an exploded view of your mesh",
    "author": "Shawn Shipley",
    "version": (1, 0, 5),
    "blender": (4, 2, 0),
    "category": "3D View",
    "doc_url": "https://github.com/shawnshipley/explodium",
    "support": "Community",
}

from .explodium import *


def register():
    explodium.register()


def unregister():
    explodium.unregister()


if __name__ == "__main__":
    register()

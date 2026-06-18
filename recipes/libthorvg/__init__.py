# recipes/libthorvg/__init__.py
"""
Пустой рецепт для libthorvg (отключает сборку)
"""
from pythonforandroid.recipe import Recipe


class LibThorvgRecipe(Recipe):
    """Пустой рецепт для libthorvg - ничего не делает"""
    version = '0.0.0'
    url = 'none'
    depends = []

    def should_build(self, arch):
        return False

    def build_arch(self, arch):
        pass


recipe = LibThorvgRecipe()
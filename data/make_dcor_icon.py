"""Gera data/dcor.ico a partir do icone.png da pasta do DCOR (pixel art: aumenta sem suavizar). Precisa do Pillow."""
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), 'icone.png')


def square(im, size):
    """Maior múltiplo inteiro que cabe em size (pixels nítidos), centralizado num quadrado transparente."""
    k = max(1, size // max(im.size))
    big = im.resize((im.width * k, im.height * k), Image.NEAREST)
    if max(big.size) > size:
        big = im.resize((size * im.width // max(im.size), size * im.height // max(im.size)), Image.LANCZOS)
    out = Image.new('RGBA', (size, size))
    out.paste(big, ((size - big.width) // 2, (size - big.height) // 2))
    return out


def main():
    im = Image.open(SRC).convert('RGBA')
    sizes = [256, 128, 64, 48, 32, 16]
    imgs = [square(im, s) for s in sizes]
    imgs[0].save(os.path.join(HERE, 'dcor.ico'), sizes=[(s, s) for s in sizes], append_images=imgs[1:])
    print('->', os.path.join(HERE, 'dcor.ico'))


if __name__ == '__main__':
    main()

import pytest
from packaging.version import parse as parse_version

from PIL import Image, features

from .helper import assert_image_similar, hopper, is_ppc64le, skip_unless_feature


def test_sanity():
    image = hopper()
    converted = image.quantize()
    assert converted.mode == "P"
    assert_image_similar(converted.convert("RGB"), image, 10)

    image = hopper()
    converted = image.quantize(palette=hopper("P"))
    assert converted.mode == "P"
    assert_image_similar(converted.convert("RGB"), image, 60)


@skip_unless_feature("libimagequant")
def test_libimagequant_quantize():
    image = hopper()
    if is_ppc64le():
        libimagequant = parse_version(features.version_feature("libimagequant"))
        if libimagequant < parse_version("4"):
            pytest.skip("Fails with libimagequant earlier than 4.0.0 on ppc64le")
    converted = image.quantize(100, Image.LIBIMAGEQUANT)
    assert converted.mode == "P"
    assert_image_similar(converted.convert("RGB"), image, 15)
    assert len(converted.getcolors()) == 100


def test_octree_quantize():
    image = hopper()
    converted = image.quantize(100, Image.FASTOCTREE)
    assert converted.mode == "P"
    assert_image_similar(converted.convert("RGB"), image, 20)
    assert len(converted.getcolors()) == 100


def test_rgba_quantize():
    image = hopper("RGBA")
    with pytest.raises(ValueError):
        image.quantize(method=0)

    assert image.quantize().convert().mode == "RGBA"


def test_quantize():
    with Image.open("Tests/images/caption_6_33_22.png") as image:
        image = image.convert("RGB")
    converted = image.quantize()
    assert converted.mode == "P"
    assert_image_similar(converted.convert("RGB"), image, 1)


def test_quantize_no_dither():
    image = hopper()
    with Image.open("Tests/images/caption_6_33_22.png") as palette:
        palette = palette.convert("P")

    converted = image.quantize(dither=0, palette=palette)
    assert converted.mode == "P"
    assert converted.palette.palette == palette.palette.palette


def test_quantize_dither_diff():
    image = hopper()
    with Image.open("Tests/images/caption_6_33_22.png") as palette:
        palette = palette.convert("P")

    dither = image.quantize(dither=1, palette=palette)
    nodither = image.quantize(dither=0, palette=palette)

    assert dither.tobytes() != nodither.tobytes()


def test_colors():
    im = hopper()
    colors = 2
    converted = im.quantize(colors)
    assert len(converted.palette.palette) == colors * len("RGB")


def test_transparent_colors_equal():
    im = Image.new("RGBA", (1, 2), (0, 0, 0, 0))
    px = im.load()
    px[0, 1] = (255, 255, 255, 0)

    converted = im.quantize()
    converted_px = converted.load()
    assert converted_px[0, 0] == converted_px[0, 1]


@pytest.mark.parametrize(
    "method, color",
    (
        (Image.MEDIANCUT, (0, 0, 0)),
        (Image.MAXCOVERAGE, (0, 0, 0)),
        (Image.FASTOCTREE, (0, 0, 0)),
        (Image.FASTOCTREE, (0, 0, 0, 0)),
    ),
)
def test_palette(method, color):
    im = Image.new("RGBA" if len(color) == 4 else "RGB", (1, 1), color)

    converted = im.quantize(method=method)
    converted_px = converted.load()
    assert converted_px[0, 0] == converted.palette.colors[color]

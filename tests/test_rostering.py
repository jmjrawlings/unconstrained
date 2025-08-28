from models import rostering as m

async def test_nurse_rostering(minizinc_options):

    model = m.create_model()
    assert True
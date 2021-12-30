import pytest
from resilient_async_cts.dto.artifact_property_dto import ArtifactPropertyDTO, InvalidPropertyKey, ValueTypeMismatch, PropertyTypeNotSupported

class TestArtifactPropertyDTO():

    def test_valid_string(self):
        x = ArtifactPropertyDTO('string', 'test', 'test')

        assert type(x) == ArtifactPropertyDTO

    def test_invalid_string(self):
        with pytest.raises(ValueTypeMismatch):
            ArtifactPropertyDTO('string', 'test', 33)

    def test_valid_number(self):
        x = ArtifactPropertyDTO('number', 'test', 4)

        assert type(x) == ArtifactPropertyDTO

    def test_invalid_number(self):
        with pytest.raises(ValueTypeMismatch):
            ArtifactPropertyDTO('number', 'test', '33')

    def test_valid_uri(self):
        x = ArtifactPropertyDTO('uri', 'test', 'https://example.com')

        assert type(x) == ArtifactPropertyDTO
    
    def test_invalid_uri(self):
        with pytest.raises(ValueTypeMismatch):
            ArtifactPropertyDTO('uri', 'test', 33)

    def test_valid_ip(self):
        x =  ArtifactPropertyDTO('ip', 'test', '10.10.10.1')

        assert type(x) == ArtifactPropertyDTO

    def test_invalid_ip(self):
        with pytest.raises(ValueTypeMismatch):
            ArtifactPropertyDTO('ip', 'test', {'ip': '10.0.0.1'})
    
    def test_valid_lat_lng(self):
        lat_lng = {
            'lat': 43,
            'lng': -88
        }

        x =  ArtifactPropertyDTO('lat_lng', 'test', lat_lng)

        assert type(x) == ArtifactPropertyDTO

    def test_invalid_lat_lng(self):
        with pytest.raises(ValueTypeMismatch):
            ArtifactPropertyDTO('lat_lng', 'test', [43, -88])

    def test_unsupported_type(self):
        with pytest.raises(PropertyTypeNotSupported):
            ArtifactPropertyDTO('test', 'test', 'test')

    def test_valid_property_key_change(self):
        x = ArtifactPropertyDTO('string', 'test', 'test')

        x['name'] = 'changed_my_mind'

        assert(True)

    def test_invalid_property_key(self):
        with pytest.raises(InvalidPropertyKey):
            x = ArtifactPropertyDTO('string', 'test', 'test')

            x['test'] = 'hello world'
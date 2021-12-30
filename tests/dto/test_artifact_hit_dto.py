import pytest
from resilient_async_cts.dto.artifact_hit_dto import ArtifactHitDTO, InvalidPropertyType, DuplicatePropertyName
from resilient_async_cts.dto.artifact_property_dto import ArtifactPropertyDTO

class TestArtifactHitDTO():

    def test_valid_hit_dto(self):
        """Testing valid ArtifactHitDTO"""
        properties = [
            ArtifactPropertyDTO('string', 'test', 'test'),
            ArtifactPropertyDTO('string', 'test2', 'test2')
        ]

        x = ArtifactHitDTO(properties)

        assert type(x) == ArtifactHitDTO

    def test_no_property_dto(self):
        """Testing non ArtifactHitDTO supplied"""
        with pytest.raises(InvalidPropertyType):
            properties = [
                {
                    "type": "string",
                    "name": "test",
                    "value": "test"
                }
            ]

            ArtifactHitDTO(properties)

    def test_duplicate_property_names(self):
        """Testing multiple properties with the same name"""
        with pytest.raises(DuplicatePropertyName):
            properties = [
                ArtifactPropertyDTO('string', 'test', 'test'),
                ArtifactPropertyDTO('string', 'test', 'test')
            ]

            ArtifactHitDTO(properties)

    def test_mixed_property_types(self):
        """Testing if a ArtifactPropertyDTO and a dict are passed"""
        with pytest.raises(InvalidPropertyType):
            properties = [
                ArtifactPropertyDTO('string', 'test', 'test'),
                {
                    'type': 'string',
                    'name': 'test2',
                    'value': 'test'
                }
            ]

            ArtifactHitDTO(properties)
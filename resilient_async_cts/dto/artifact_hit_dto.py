from .artifact_property_dto import ArtifactPropertyDTO
from ..exceptions import BaseAsyncCTSError

class ArtifactHitDTO(list):
    """
    Represents a 'hit' from the CTS. A hit is made up of one or more 
    ArtifactPropertyDTO objects, where each ArtifactPropertyDTO is a property
    of the hit.
    """

    def __init__(self, props):
        """
        :param array<ArtifactPropertyDTO>: list of artifact propertiy DTOs
        """
        self.unique_names(props)
        self.verify_props_type(props)
        super().__init__(props)

    def unique_names(self, props):
        """
        Makes sure that all of the AritfaquitctPropertyDTO objects have unique 
        names.

        :param array<ArtifactPropertyDTO>: list of artifact propertiy DTOs
        """
        seen_names = []

        for prop in props:
            if (prop.get('name') in seen_names):
                raise DuplicatePropertyName(f"There are multiple properties with the name '{prop.get('name')}'. Property names must be unique within the ArtifactHitDTO")
            else:
                seen_names.append(prop.get('name'))
    
    def verify_props_type(self, props):
        """
        Checks the type of each property within the list to verify it is an
        instance of ArtifactHitDTO.

        :param list<ArtifactPropertyDTO>: list of artifact property DTOs
        :raises InvalidPropertyType if a property is passed in that isn't an
        instance of ArtifactHitDTO
        """
        for prop in props:
            if (type(prop) != ArtifactPropertyDTO):
                raise InvalidPropertyType()

    def check_new_property(self, new_prop):
        """
        Checks the property that is attempted to be added to verify that it's
        an instance of ArtifactHitDTO and that the property name has not 
        already been used.
        :param ArtifactPropertyDTO new_prop: the property to add
        """
        self.verify_props_type([new_prop])

        for prop in self:
            if prop.get('name') == new_prop.get('name'):
                raise DuplicatePropertyName(f"There is already a property with the name '{new_prop.get('name')}'")

    def append(self, new_prop):
        """
        Appends the property to the end of the ArtifactHitDTO object

        :param ArtifactPropertyDTO new_prop: the property to append
        """
        self.check_new_property(new_prop)
        super(ArtifactHitDTO, self).append(new_prop)
        
class InvalidPropertyType(BaseAsyncCTSError):

    def __init__(self):
        super().__init__(self, "Properties must be an instance of ArtifactHitDTO")

class DuplicatePropertyName(BaseAsyncCTSError):

    def __init__(self, message):
        super().__init__(self, message)

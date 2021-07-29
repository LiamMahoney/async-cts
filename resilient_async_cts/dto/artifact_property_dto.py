from ..exceptions import BaseAsyncCTSError

SUPPORTED_TYPES = [
    'string',
    'number',
    'uri',
    'ip',
    'lat_lang'
]

VALID_KEYS = ['type', 'name', 'value']

class ArtifactPropertyDTO(dict):
    """
    A single property of an ArtifactHitDTO. ArtifactPropertyDTOs describe the
    type, name and value of the property.

    :param string type: the type of the property string|number|uri|ip|lat_lang
    :param string name: the name of the property
    :param string|int|dict value: the value of the property
    """

    def __init__(self, type, name, value):
        """
        :param string type: the type of the property
        :param string name: the name of the property
        :param string | int | dict value: the value of the property
        """
        self.supported_type(type)
        self.types_match(type, value)
        super().__init__({
            'type': type,
            'name': name,
            'value': value
        })

    def supported_type(self, type):
        """
        Verifies that the type is a valid selection.

        :raises PropertyTypeNotSupported
        """
        if (type not in SUPPORTED_TYPES):
            raise PropertyTypeNotSupported()
    
    def types_match(self, prop_type, value):
        """
        Makes sure that the type and the type of the value match.

        :param string type: the type of the property
        :param string | int | dict value: the value of the property
        :raises ValueTypeMismatch when the property type adn the type of the 
        value do not match
        """
        if (prop_type == 'string' and type(value) != str):
            raise ValueTypeMismatch(prop_type, value)
        elif (prop_type == 'number' and type(value) != int):
            raise ValueTypeMismatch(prop_type, value)
        elif (prop_type == 'uri' and type(value) != str):
            raise ValueTypeMismatch(prop_type, value)
        elif (prop_type == 'ip' and type(value) != str):
            raise ValueTypeMismatch(prop_type, value)
        elif (prop_type == 'lat_lng' and type(value) != dict):
            raise ValueTypeMismatch(prop_type, value)
    
    def __setitem__(self, key, value):
        """
        Only allows keys with a value of 'type', 'name' or 'value' to be added.

        :raises InvalidPropertyKey if a key/value pair is added with a key
        that isn't valid
        """
        if (key not in VALID_KEYS):
            raise InvalidPropertyKey(key)
        
        super().__setitem__(key, value)

class InvalidPropertyKey(BaseAsyncCTSError):

    def __init__(self, key):
        super().__init__(self, f"{key} is not a valid key for a ArtifactPropertyDTO. Valid keys are {VALID_KEYS}")    

class PropertyTypeNotSupported(BaseAsyncCTSError):

    def __init__(self):
        super().__init__(self, f"Property type must be one of {SUPPORTED_TYPES}")

class ValueTypeMismatch(BaseAsyncCTSError):

    def __init__(self, prop_type, value):
        super().__init__(self, f"the property type {prop_type} and value {value} (type {type(value)}) do not match")
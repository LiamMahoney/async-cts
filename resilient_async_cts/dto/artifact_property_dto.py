class ArtifactPropertyDTO(dict):
    """
    TODO:
    """

    supported_types = [
            'string',
            'number',
            'uri',
            'ip',
            'lat_lang'
        ]

    def __init__(self, type, name, value):
        """
        TODO: see if I can make this async
        :parm string type: the type of the property
        :param string name: the name of the property
        :param string | int | dict value: the value of the property
        """
        self.supported_type(type)
        self.types_match(type, value)
        self.__dict__ = self
        self.__dict__['type'] = type
        self.__dict__['name'] = name
        self.__dict__['value'] = value

    def supported_type(self, type):
        """
        Verifies that the type is a valid selection.

        :raises PropertyTypeNotSupported
        """
        if (type not in self.supported_types):
            raise PropertyTypeNotSupported(self.supported_types)
    
    def types_match(self, prop_type, value):
        """
        Makes sure that the type and the type of the value match.

        :param string type: the type of the property
        :param string | int | dict value: the value of the property
        """
        if (prop_type == 'string' and type(value) != str):
            raise ValueTypeMismatch(type, value)
        elif (prop_type == 'number' and type(value) != int):
            raise ValueTypeMismatch(type, value)
        elif (prop_type == 'uri' and type(value) != str):
            raise ValueTypeMismatch(type, value)
        elif (prop_type == 'ip' and type(value) != str):
            raise ValueTypeMismatch(type, value)
        elif (prop_type == 'lat_lng' and type(value) != dict):
            raise ValueTypeMismatch(type, value)

    def __getitem(self, key):
        return self.__dict__[key]

class PropertyTypeNotSupported(Exception):

    def __init__(self, supported_types):
        Exception.__init__(self, f"Property type must be one of {supported_types}")

class ValueTypeMismatch(Exception):

    def __init__(self, type, value):
        Exception.__init__(self, f"the type {type} and value {value} do not match")
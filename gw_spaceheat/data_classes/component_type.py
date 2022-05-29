""" ComponentType Class Definition """

from data_classes.component_type_base import ComponentTypeBase

from data_classes.component_sub_category import ComponentSubCategory #
from data_classes.component_sub_category_static import PlatformComponentSubCategory #

class ComponentType(ComponentTypeBase):


    """ Derived attributes """  
    @property
    def component_category(self) -> str:
        raise NotImplementedError


    """Static foreign objects referenced by their keys """

    @property
    def component_sub_category(self):
        if (self.component_sub_category_value is None):
            return None
        elif not(self.component_sub_category_value in PlatformComponentSubCategory.keys()):
            raise TypeError('ComponentSubCategory must belong to Static List')
        else:  
            return PlatformComponentSubCategory[self.component_sub_category_value]      


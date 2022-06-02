""" ComponentType Class Definition """

from data_classes.component_sub_category_static import \
    PlatformComponentSubCategory
from data_classes.component_type_base import ComponentTypeBase


class ComponentType(ComponentTypeBase):

    @property
    def component_category(self) -> str:
        raise NotImplementedError

    @property
    def component_sub_category(self):
        if (self.component_sub_category_value is None):
            return None
        elif not(self.component_sub_category_value in PlatformComponentSubCategory.keys()):
            raise TypeError('ComponentSubCategory must belong to Static List')
        else:  
            return PlatformComponentSubCategory[self.component_sub_category_value]      


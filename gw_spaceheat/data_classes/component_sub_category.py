""" ComponentSubCategory Class Definition """

from data_classes.component_sub_category_base import ComponentSubCategoryBase

from data_classes.component_category import ComponentCategory #
from data_classes.component_category_static import PlatformComponentCategory #

class ComponentSubCategory(ComponentSubCategoryBase):


    """ Derived attributes """  

    """Static foreign objects referenced by their keys """

    @property
    def component_category(self):
        if (self.component_category_value is None):
            return None
        elif not(self.component_category_value in PlatformComponentCategory.keys()):
            raise TypeError('ComponentCategory must belong to Static List')
        else:  
            return PlatformComponentCategory[self.component_category_value]      


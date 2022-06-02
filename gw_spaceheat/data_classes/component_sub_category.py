""" ComponentSubCategory Class Definition """
from data_classes.component_category_static import PlatformComponentCategory
from data_classes.component_sub_category_base import ComponentSubCategoryBase


class ComponentSubCategory(ComponentSubCategoryBase):
    
    @property
    def component_category(self):
        if (self.component_category_value is None):
            return None
        elif not(self.component_category_value in PlatformComponentCategory.keys()):
            raise TypeError('ComponentCategory must belong to Static List')
        else:  
            return PlatformComponentCategory[self.component_category_value]      


<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:msxsl="urn:schemas-microsoft-com:xslt" exclude-result-prefixes="msxsl" xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xsl:output method="xml" indent="yes" />
    <xsl:param name="root" />
    <xsl:param name="codee-root" />
    <xsl:include href="../CommonXsltTemplates.xslt"/>
    <xsl:param name="exclude-collections" select="'false'" />
    <xsl:param name="relationship-suffix" select="''" />
    <xsl:variable name="airtable" select="document('Airtable.xml')" />
    <xsl:variable name="odxml" select="/" />
    <xsl:variable name="squot">'</xsl:variable>
    <xsl:variable name="init-space">             </xsl:variable>
    <xsl:include href="GwSchemaCommon.xslt"/>

    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
        </xsl:copy>
    </xsl:template>

    <xsl:template match="/">
        <FileSet>
            <FileSetFiles>
                <xsl:for-each select="$airtable//GwEntities/GwEntity[ScadaUses = 'true']">
                    <xsl:variable name="entity" select="." />
                    <xsl:variable name="od" select="$odxml//ObjectDefs/ObjectDef[Name=$entity/Name]"/>
                    <xsl:variable name="lower-name" select="translate(Name, $ucletters, $lcletters)" />
                    <xsl:variable name="python-odname">
                        <xsl:call-template name="python-case"><xsl:with-param name="camel-case-text" select="Name"  /></xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="primary-key-name">
                        <xsl:call-template name="python-case"><xsl:with-param name="camel-case-text" select="$entity/PrimaryKeyName"/> </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="read-only-properties" select="$od//PropertyDef[(normalize-space(IsReadonly) = 'true' or normalize-space(MatchingMetaData/IsReadonly) = 'true')]"/>
                    <xsl:variable name="basic-properties" select="$od//PropertyDef[normalize-space(IsCollection) != 'true' and normalize-space(MatchingMetaData/IsCollection) != 'true' and normalize-space(IsReadonly) != 'true' and normalize-space(MatchingMetaData/IsReadonly) != 'true' and IsPrimaryKey = 0 and count(Relationships)=0 and Name != 'Definition' and Name !='Description' ]"/>
                    <xsl:variable name="foreign-keys" select="$od//PropertyDef[normalize-space(MatchingMetaData/RelationshipType)='One' and normalize-space(IsCollection) != 'true' and count(Relationships)>0 and normalize-space(MatchingMetaData/IsCollection) != 'true']"/> 
                    <FileSetFile>
                        <xsl:element name="RelativePath"><xsl:text>../../../gw_spaceheat/data_classes/</xsl:text><xsl:value-of select="$python-odname"   /><xsl:text>.py</xsl:text></xsl:element>
                        <OverwriteMode>Never</OverwriteMode>
                        <xsl:element name="FileContents"><xsl:text>""" </xsl:text><xsl:value-of select="$od/Name" /><xsl:text> Class Definition """

from data_classes.</xsl:text><xsl:value-of select="$python-odname"/><xsl:text>_base import </xsl:text><xsl:value-of select="$od/Name" /><xsl:text>Base

</xsl:text>
<xsl:for-each select="$foreign-keys">
<xsl:variable name="foreign-object-name" select="Relationships/Relationship/ReferencedObjectDef"/>    
<xsl:variable name="foreign-gw-entity" select="$airtable//GwEntities/GwEntity[Name=$foreign-object-name]"/>
<xsl:text>from data_classes.</xsl:text>
<xsl:call-template name="python-case">
    <xsl:with-param name="camel-case-text" select="$foreign-gw-entity/Name"  />
</xsl:call-template>
<xsl:text> import </xsl:text><xsl:value-of select="$foreign-gw-entity/Name"/>
<xsl:text> #
</xsl:text>
<xsl:if test="$foreign-gw-entity/AllObjectsStaticBool = 1">
<xsl:text>from data_classes.</xsl:text>
<xsl:call-template name="python-case">
    <xsl:with-param name="camel-case-text" select="$foreign-gw-entity/Name"  />
</xsl:call-template><xsl:text>_static import Platform</xsl:text><xsl:value-of select="$foreign-gw-entity/Name"/>
<xsl:text> #
</xsl:text>
</xsl:if>

</xsl:for-each>
<xsl:text>
class </xsl:text><xsl:value-of select="$od/Name" /><xsl:text>(</xsl:text><xsl:value-of select="$od/Name" /><xsl:text>Base):
</xsl:text>
<xsl:if test="$entity/AllObjectsStaticBool = 0">
<xsl:text>
    @classmethod
    def check_existence_of_certain_attributes(cls, attributes):
        if not '</xsl:text><xsl:value-of select="$python-odname"/><xsl:text>_id' in attributes.keys():
            raise Exception('</xsl:text><xsl:value-of select="$python-odname"/><xsl:text>_id must exist')       

    @classmethod
    def check_initialization_consistency(cls, attributes):
        </xsl:text><xsl:value-of select="$od/Name" /><xsl:text>.check_uniqueness_of_primary_key(attributes)
        </xsl:text><xsl:value-of select="$od/Name" /><xsl:text>.check_existence_of_certain_attributes(attributes)
    
    def check_immutability_for_existing_attributes(self, new_attributes):
        if self.</xsl:text><xsl:value-of select="$python-odname"/><xsl:text>_id:
            if new_attributes['</xsl:text><xsl:value-of select="$python-odname"/><xsl:text>_id'] != self.</xsl:text><xsl:value-of select="$python-odname"/><xsl:text>_id:
                raise Exception('</xsl:text><xsl:value-of select="$python-odname"/><xsl:text>_id is Immutable')

    def check_update_consistency(self, new_attributes):
        self.check_immutability_for_existing_attributes(new_attributes)
</xsl:text>
</xsl:if>
<xsl:text>

    """ Derived attributes """  
</xsl:text>

<xsl:for-each select="$read-only-properties">
<xsl:text>    @property
    def </xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Name"  />
        </xsl:call-template><xsl:text>(self) -> str:
        raise NotImplementedError

</xsl:text>
    
</xsl:for-each>
<xsl:text>
    """Static foreign objects referenced by their keys """

</xsl:text>
<xsl:for-each select="$foreign-keys">
    <xsl:variable name="foreign-object-name" select="Relationships/Relationship/ReferencedObjectDef"/>    
    <xsl:variable name="foreign-gw-entity" select="$airtable//GwEntities/GwEntity[Name=$foreign-object-name]"/>
    <xsl:if test="$foreign-gw-entity/AllObjectsStaticBool = 1">
    <xsl:variable name="primary-key">
        <xsl:call-template name="python-case">   
            <xsl:with-param name="camel-case-text" select="Name"  />
        </xsl:call-template><xsl:text>_</xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="$foreign-gw-entity/PrimaryKeyName"/>
        </xsl:call-template>
    </xsl:variable>
    <xsl:text>    @property
    def </xsl:text>
    <xsl:call-template name="python-case">
        <xsl:with-param name="camel-case-text" select="Name"  />
    </xsl:call-template>
    <xsl:text>(self):
        if (self.</xsl:text><xsl:value-of select="$primary-key"/><xsl:text> is None):
            return None
        elif not(self.</xsl:text><xsl:value-of select="$primary-key"/><xsl:text> in Platform</xsl:text>
        <xsl:value-of select="$foreign-gw-entity/Name"/><xsl:text>.keys()):
            raise TypeError('</xsl:text><xsl:value-of select="$foreign-gw-entity/Name"/><xsl:text> must belong to Static List')
        else:  
            return Platform</xsl:text><xsl:value-of select="$foreign-gw-entity/Name"/><xsl:text>[self.</xsl:text>
        <xsl:value-of select="$primary-key"/>  <xsl:text>]      

</xsl:text>

    </xsl:if>   

</xsl:for-each>
</xsl:element>
                    </FileSetFile>

                </xsl:for-each>

            </FileSetFiles>
        </FileSet>
    </xsl:template>
    <xsl:template name="get-default-value">
        <xsl:param name="propertyDef" />
        <xsl:variable name="uc-type" select="translate($propertyDef/DataType, $lcletters, $ucletters)" />
        <xsl:choose>
            <xsl:when test="$uc-type = 'NTEXT' or $uc-type = 'TEXT' or $uc-type = 'STRING'"><xsl:text>Optional[str] = None</xsl:text>
            </xsl:when>
            <xsl:when test="$uc-type = 'INT16' or $uc-type = 'INT32' or $uc-type = 'INT64' or $uc-type = 'INT' or $uc-type = 'DATE' or $uc-type = 'DATETIME'"><xsl:text>Optional[int] = None</xsl:text></xsl:when>
            <xsl:when test="$uc-type = 'BOOLEAN' or $uc-type = 'BOOL'"><xsl:text>Optional[bool] = None</xsl:text></xsl:when>
            <xsl:when test="$uc-type = 'DECIMAL' or $uc-type = 'FLOAT' or $uc-type = 'NUMBER'"><xsl:text>Optional[float] = None</xsl:text> </xsl:when>
            <xsl:otherwise><xsl:text>None</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    



    
</xsl:stylesheet>
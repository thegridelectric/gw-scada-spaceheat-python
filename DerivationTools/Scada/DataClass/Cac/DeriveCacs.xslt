<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:msxsl="urn:schemas-microsoft-com:xslt" exclude-result-prefixes="msxsl" xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xsl:output method="xml" indent="yes" />
    <xsl:param name="root" />
    <xsl:param name="codee-root" />
    <xsl:include href="../CommonXsltTemplates.xslt"/>
    <xsl:param name="exclude-collections" select="'false'" />
    <xsl:param name="relationship-suffix" select="''" />
    <xsl:variable name="airtable" select="/" />
    <xsl:variable name="squot">'</xsl:variable>
    <xsl:variable name="init-space">             </xsl:variable>
    <xsl:include href="ScadaCommon.xslt"/>

    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
        </xsl:copy>
    </xsl:template>

    <xsl:template match="/">
        <FileSet>
            <FileSetFiles>
                <xsl:for-each select="$airtable//Schemas/Schema[(normalize-space(Alias) !='') and (MakeDataClass='true')  and (IsCac='true') and (Status = 'Active')]"> 
                    <xsl:variable name="schema-id" select="SchemaId" />  
                    <xsl:variable name="class-name">
                        <xsl:call-template name="nt-case">
                            <xsl:with-param name="mp-schema-text" select="AliasRoot" />
                        </xsl:call-template>
                    </xsl:variable>
                    <FileSetFile>
                                <xsl:element name="RelativePath"><xsl:text>../../../../gw_spaceheat/data_classes/cacs/</xsl:text>
                                <xsl:call-template name="python-case">
                                    <xsl:with-param name="camel-case-text" select="DataClass"  />
                                </xsl:call-template><xsl:text>.py</xsl:text></xsl:element>

                        <OverwriteMode>Never</OverwriteMode>
                        <xsl:element name="FileContents">

   
<xsl:text>"""</xsl:text><xsl:value-of select="DataClass"/><xsl:text> definition"""
from typing import Dict, Optional

from data_classes.component_attribute_class import ComponentAttributeClass
from data_classes.cacs.</xsl:text>
<xsl:call-template name="python-case">
    <xsl:with-param name="camel-case-text" select="DataClass"  />
</xsl:call-template><xsl:text>_base import </xsl:text>
<xsl:value-of select="DataClass"/><xsl:text>Base
from schema.gt.</xsl:text> <xsl:value-of select="translate(AliasRoot,'.','_')"/>
<xsl:text>.</xsl:text><xsl:value-of select="translate(AliasRoot,'.','_')"/>
<xsl:text> import </xsl:text><xsl:value-of select="$class-name"/><xsl:text>


class </xsl:text><xsl:value-of select="DataClass"/><xsl:text>(</xsl:text>
<xsl:value-of select="DataClass"/><xsl:text>Base):
    by_id: Dict[str, "</xsl:text><xsl:value-of select="DataClass"/><xsl:text>"] = {}

    def __init__(self, </xsl:text>
    <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsPrimitive = 'true') and (IsRequired = 'true')]">
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template><xsl:text>: </xsl:text>
        <xsl:call-template name="python-type">
            <xsl:with-param name="gw-type" select="PrimitiveType"/>
        </xsl:call-template>
    <xsl:text>,
                 </xsl:text>
    </xsl:for-each>
    <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (normalize-space(EnumLocalName) != '')]">
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template><xsl:text>_gt_enum_symbol: str,
                 </xsl:text>
    </xsl:for-each>
    <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsPrimitive = 'true') and  not(IsRequired = 'true')]">
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template><xsl:text>: Optional[</xsl:text>
        <xsl:call-template name="python-type">
            <xsl:with-param name="gw-type" select="PrimitiveType"/>
        </xsl:call-template>
        <xsl:text>] = None,
                 </xsl:text>
</xsl:for-each>
    <xsl:text>):
        super(self.__class__, self).__init__(</xsl:text>
        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (normalize-space(EnumLocalName) = '') ]">
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template><xsl:text>=</xsl:text>
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template><xsl:text>,
                                             </xsl:text>
        </xsl:for-each>
        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (normalize-space(EnumLocalName) != '') ]">
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template><xsl:text>_gt_enum_symbol=</xsl:text>
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template><xsl:text>_gt_enum_symbol,
                                             </xsl:text>
        </xsl:for-each>
        <xsl:text>)
        </xsl:text><xsl:value-of select="DataClass"/><xsl:text>.by_id[self.component_attribute_class_id] = self
        ComponentAttributeClass.by_id[self.component_attribute_class_id] = self

    def _check_update_axioms(self, type: </xsl:text><xsl:value-of select="$class-name"/><xsl:text>):
        pass

    def __repr__(self):
        return f"{self.make_model.value} {self.display_name}"
</xsl:text>


                        </xsl:element>
                     </FileSetFile>
                </xsl:for-each>

            </FileSetFiles>
        </FileSet>
    </xsl:template>


</xsl:stylesheet>
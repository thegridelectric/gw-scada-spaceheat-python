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
                <xsl:for-each select="$airtable//Schemas/Schema[(normalize-space(Alias) !='') and (MakeDataClass='true')  and (Status = 'Active')]">
                <xsl:variable name="schema-alias" select="Alias" />
                <xsl:variable name="schema-id" select="SchemaId" />  
                <xsl:variable name="class-name">
                    <xsl:call-template name="nt-case">
                        <xsl:with-param name="mp-schema-text" select="Alias" />
                    </xsl:call-template>
                </xsl:variable>
                <xsl:variable name="python-data-class">
                    <xsl:call-template name="python-case">
                        <xsl:with-param name="camel-case-text" select="translate(DataClass,'.','_')"  />
                    </xsl:call-template>
                </xsl:variable>
                <xsl:variable name="data-class-id">
                    <xsl:if test="IsCac='true'">
                        <xsl:text>component_attribute_class_id</xsl:text>
                    </xsl:if>
                    <xsl:if test="IsComponent='true'">
                        <xsl:text>component_id</xsl:text>
                    </xsl:if>
                    
                    <xsl:if test="not (IsCac='true') and not (IsComponent='true')">
                        <xsl:value-of select="$python-data-class"/><xsl:text>_id</xsl:text>
                   </xsl:if>
                </xsl:variable>
                <FileSetFile>
                            <xsl:element name="RelativePath"><xsl:text>../../../../gw_spaceheat/schema/gt/</xsl:text>
                            <xsl:value-of select="translate(AliasRoot,'.','_')"/><xsl:text>/</xsl:text>
                            <xsl:value-of select="translate(AliasRoot,'.','_')"/><xsl:text>_maker.py</xsl:text></xsl:element>

                    <OverwriteMode>Always</OverwriteMode>
                    <xsl:element name="FileContents">

<xsl:text>"""Makes </xsl:text><xsl:value-of select="$schema-alias"/><xsl:text> type"""
# length of GtBooleanActuatorComponent100: </xsl:text><xsl:value-of select="string-length($class-name)"/>
<xsl:text>
from typing import Dict, Optional</xsl:text>

<xsl:if test="IsCac = 'true'">
<xsl:text>
from data_classes.cacs.</xsl:text>
<xsl:value-of select="$python-data-class"/>
<xsl:text> import </xsl:text><xsl:value-of select="DataClass"/>
</xsl:if>
<xsl:if test="IsComponent = 'true'">
<xsl:text>
from data_classes.components.</xsl:text>
<xsl:value-of select="$python-data-class"/>
<xsl:text> import </xsl:text><xsl:value-of select="DataClass"/>
</xsl:if>
<xsl:if test="not(IsComponent = 'true') and not(IsCac = 'true')">
<xsl:text>
from data_classes.</xsl:text>
<xsl:value-of select="$python-data-class"/>
<xsl:text> import </xsl:text><xsl:value-of select="DataClass"/>
</xsl:if>
<xsl:text>

from schema.gt.</xsl:text> <xsl:value-of select="translate(AliasRoot,'.','_')"/>
<xsl:text>.</xsl:text><xsl:value-of select="translate(Alias,'.','_')"/>
<xsl:text> import </xsl:text><xsl:value-of select="$class-name"/><xsl:text>
from schema.errors import MpSchemaError</xsl:text>

<xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsEnum = 'true')]">
<xsl:text>
from schema.enums.</xsl:text>
<xsl:call-template name="python-case">
    <xsl:with-param name="camel-case-text" select="translate(EnumLocalName,'.','_')"  />
</xsl:call-template>
<xsl:text>.</xsl:text>
<xsl:call-template name="python-case">
    <xsl:with-param name="camel-case-text" select="translate(EnumLocalName,'.','_')"  />
</xsl:call-template>
<xsl:text>_map import </xsl:text>
    <xsl:call-template name="nt-case">
        <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
    </xsl:call-template>
<xsl:text>, </xsl:text>
<xsl:call-template name="nt-case">
    <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
</xsl:call-template>
<xsl:text>Map</xsl:text>
</xsl:for-each>
<xsl:text>


class </xsl:text>
<xsl:call-template name="nt-case">
                        <xsl:with-param name="mp-schema-text" select="AliasRoot" />
                    </xsl:call-template>
<xsl:text>_Maker():

    def __init__(self</xsl:text>
    <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsPrimitive = 'true') and (IsRequired = 'true')]">
                <xsl:text>,
                 </xsl:text>
                <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template><xsl:text>: </xsl:text>
        <xsl:call-template name="python-type">
            <xsl:with-param name="gw-type" select="PrimitiveType"/>
        </xsl:call-template>
    </xsl:for-each>
    <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsEnum = 'true')]">
                <xsl:text>,
                 </xsl:text>
                <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template><xsl:text>: </xsl:text>
        <xsl:call-template name="nt-case">
                        <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
        </xsl:call-template>
    </xsl:for-each>
    <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsType = 'true')]">
                <xsl:text>,
                 </xsl:text>
                <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template><xsl:text>_id: str</xsl:text>
    </xsl:for-each>
    <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsPrimitive = 'true') and not (IsRequired = 'true')]">
                <xsl:text>,
                 </xsl:text>
                <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template><xsl:text>: Optional[</xsl:text>
            <xsl:call-template name="python-type">
            <xsl:with-param name="gw-type" select="PrimitiveType"/>
            </xsl:call-template><xsl:text>]</xsl:text>
            </xsl:for-each>
    <xsl:text>):

        t = </xsl:text><xsl:value-of select="$class-name"/>
        <xsl:text>(</xsl:text>
        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and ((IsPrimitive = 'true') or (IsEnum = 'true'))]">
        <xsl:value-of select="Value"/><xsl:text>=</xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template><xsl:text>,
                                          </xsl:text>
        </xsl:for-each>
        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsType = 'true')]">
        <xsl:value-of select="Value"/><xsl:text>Id=</xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
<xsl:text>_id,
                                          </xsl:text>
    </xsl:for-each>
    <xsl:text>)
        t.check_for_errors()
        self.type = t

    @classmethod
    def dict_to_tuple(cls, d: Dict) -> </xsl:text><xsl:value-of select="$class-name"/>
    <xsl:text>:</xsl:text>
<xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsPrimitive = 'true') and (IsRequired = 'true')]">
<xsl:text>
        if "</xsl:text><xsl:value-of select="Value"/><xsl:text>" not in d.keys():
            raise MpSchemaError(f"dict {d} missing </xsl:text>
            <xsl:value-of select="Value"/>
            <xsl:text>")</xsl:text>
</xsl:for-each>
<xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsType = 'true')]">
<xsl:text>
        if "</xsl:text><xsl:value-of select="Value"/><xsl:text>Id" not in d.keys():
            raise MpSchemaError(f"dict {d} missing </xsl:text>
            <xsl:value-of select="Value"/>
            <xsl:text>Id")</xsl:text>
</xsl:for-each>
<xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsEnum = 'true')]">
<xsl:text>
        if "</xsl:text>
        <xsl:call-template name="nt-case">
            <xsl:with-param name="mp-schema-text" select="EnumRoot" />
        </xsl:call-template><xsl:text>GtEnumSymbol" not in d.keys():
            raise MpSchemaError(f"dict {d} missing </xsl:text>
            <xsl:call-template name="nt-case">
            <xsl:with-param name="mp-schema-text" select="EnumRoot" />
        </xsl:call-template>
            <xsl:text>GtEnumSymbol")
        d["</xsl:text> <xsl:call-template name="nt-case">
            <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
        </xsl:call-template><xsl:text>"] = </xsl:text>
        <xsl:call-template name="nt-case">
            <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
        </xsl:call-template>
        <xsl:text>Map.gt_to_local(d["</xsl:text>
        <xsl:call-template name="nt-case">
            <xsl:with-param name="mp-schema-text" select="EnumRoot" />
        </xsl:call-template><xsl:text>GtEnumSymbol"])</xsl:text>
</xsl:for-each>
<xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsPrimitive = 'true') and not(IsRequired = 'true')]">
<xsl:text>
        if "</xsl:text><xsl:value-of select="Value"/><xsl:text>" not in d.keys():
            d["</xsl:text>
            <xsl:value-of select="Value"/>
            <xsl:text>"] = None</xsl:text>
</xsl:for-each>
<xsl:text>

        t = </xsl:text><xsl:value-of select="$class-name"/><xsl:text>(</xsl:text>
        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsPrimitive = 'true')]">
        <xsl:value-of select="Value"/><xsl:text>=d["</xsl:text>
        <xsl:value-of select="Value"/><xsl:text>"],
                                          </xsl:text>
        </xsl:for-each>
        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsType = 'true')]">
        <xsl:value-of select="Value"/><xsl:text>Id=d["</xsl:text>
        <xsl:value-of select="Value"/><xsl:text>Id"],
                                          </xsl:text>
        </xsl:for-each>
        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsEnum = 'true')]">
        <xsl:call-template name="nt-case">
            <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
        </xsl:call-template>
            <xsl:text>=d["</xsl:text>
            <xsl:call-template name="nt-case">
                <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
            </xsl:call-template>
                <xsl:text>"],
                                          </xsl:text>
        </xsl:for-each>
        <xsl:text>)
        t.check_for_errors()
        return t

    @classmethod
    def tuple_to_dc(cls, t: </xsl:text><xsl:value-of select="$class-name"/>
    <xsl:text>) -> </xsl:text><xsl:value-of select="DataClass"/><xsl:text>:
        s = {
            </xsl:text>
        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsPrimitive = 'true')]">
            <xsl:text>'</xsl:text>
                <xsl:call-template name="python-case">
                    <xsl:with-param name="camel-case-text" select="Value"  />
                </xsl:call-template><xsl:text>': t.</xsl:text>
        <xsl:value-of select="Value"/><xsl:text>,
            </xsl:text>
    </xsl:for-each>
    <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsType = 'true')]">
            <xsl:text>'</xsl:text>
                <xsl:call-template name="python-case">
                    <xsl:with-param name="camel-case-text" select="Value"  />
                </xsl:call-template><xsl:text>_id': t.</xsl:text>
        <xsl:value-of select="Value"/><xsl:text>Id,
            </xsl:text>
    </xsl:for-each>
    <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsEnum = 'true')]">
            <xsl:text>'</xsl:text>
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template><xsl:text>_gt_enum_symbol': </xsl:text>
            <xsl:call-template name="nt-case">
                <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
            </xsl:call-template>
            <xsl:text>Map.local_to_gt(t.</xsl:text>
            <xsl:call-template name="nt-case">
                <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
            </xsl:call-template><xsl:text>),</xsl:text>
     </xsl:for-each>
            <xsl:text>}
        if s['</xsl:text><xsl:value-of select="$data-class-id"/><xsl:text>'] in </xsl:text>
        <xsl:value-of select="DataClass"/><xsl:text>.by_id.keys():
            dc = </xsl:text><xsl:value-of select="DataClass"/><xsl:text>.by_id[s['</xsl:text>
            <xsl:value-of select="$data-class-id"/><xsl:text>']]
        else:
            dc = </xsl:text><xsl:value-of select="DataClass"/><xsl:text>(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: </xsl:text><xsl:value-of select="DataClass"/><xsl:text>) -> </xsl:text><xsl:value-of select="$class-name"/><xsl:text>:
        if dc is None:
            return None
        t = </xsl:text><xsl:value-of select="$class-name"/><xsl:text>(</xsl:text>
        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and ((IsPrimitive = 'true') or (IsEnum = 'true'))]">
        <xsl:value-of select="Value"/><xsl:text>=dc.</xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        <xsl:text>,
                                          </xsl:text>
    </xsl:for-each>
        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsType = 'true')]">
        <xsl:value-of select="Value"/><xsl:text>Id=dc.</xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template><xsl:text>_id,
                                          </xsl:text>
    </xsl:for-each>
       <xsl:text>)
        t.check_for_errors()
        return t

    @classmethod
    def dict_to_dc(cls, d: Dict) -> </xsl:text><xsl:value-of select="DataClass"/><xsl:text>:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))

    @classmethod
    def dc_to_dict(cls, dc: </xsl:text><xsl:value-of select="DataClass"/><xsl:text>) -> Dict:
        return cls.dc_to_tuple(dc).asdict()
    
</xsl:text>




                        </xsl:element>
                     </FileSetFile>
                </xsl:for-each>

            </FileSetFiles>
        </FileSet>
    </xsl:template>



</xsl:stylesheet>
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
                <xsl:for-each select="$airtable//GtEnums/GtEnum[(normalize-space(Alias) !='' and Status='Active')]">
                    <xsl:variable name="enum-alias" select="Alias" /> 
                    <xsl:variable name="enum-name-style" select="PythonEnumNameStyle" />  
                    <xsl:variable name="class-name">
                        <xsl:call-template name="nt-case">
                            <xsl:with-param name="mp-schema-text" select="Alias" />
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="local-class-name">
                        <xsl:call-template name="nt-case">
                            <xsl:with-param name="mp-schema-text" select="LocalName" />
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="enum-id" select="GtEnumId"/>
                    <FileSetFile>
                                <xsl:element name="RelativePath"><xsl:text>../../../../../gw_spaceheat/schema/enums/</xsl:text>
                                <xsl:value-of select="translate(LocalName,'.','_')"/><xsl:text>/</xsl:text>
                                <xsl:value-of select="translate(LocalName,'.','_')"/><xsl:text>_map.py</xsl:text></xsl:element>

                        <OverwriteMode>Always</OverwriteMode>
                        <xsl:element name="FileContents">

<xsl:text>from typing import Dict
from schema.errors import MpSchemaError
from schema.enums.</xsl:text><xsl:value-of select="translate(LocalName,'.','_')"/>
<xsl:text>.</xsl:text><xsl:value-of select="translate(Alias,'.','_')"/>
<xsl:text> import (
    </xsl:text><xsl:value-of select="$local-class-name"/>
<xsl:text>,
    </xsl:text><xsl:value-of select="$class-name"/>
<xsl:text>GtEnum,
)


class </xsl:text><xsl:value-of select="$local-class-name"/><xsl:text>GtEnum(</xsl:text>
<xsl:value-of select="$class-name"/>
<xsl:text>GtEnum):
    @classmethod
    def is_symbol(cls, candidate) -> bool:
        if candidate in cls.symbols:
            return True
        return False


class </xsl:text><xsl:value-of select="$local-class-name"/><xsl:text>Map:
    @classmethod
    def gt_to_local(cls, symbol):
        if not </xsl:text><xsl:value-of select="$local-class-name"/><xsl:text>GtEnum.is_symbol(symbol):
            raise MpSchemaError(
                f"{symbol} must belong to key of {</xsl:text><xsl:value-of select="$local-class-name"/>
                <xsl:text>Map.gt_to_local_dict}"
            )
        return cls.gt_to_local_dict[symbol]

    @classmethod
    def local_to_gt(cls, </xsl:text>
            <xsl:value-of select="translate(LocalName,'.','_')"/><xsl:text>):
        if not isinstance(</xsl:text><xsl:value-of select="translate(LocalName,'.','_')"/><xsl:text>, </xsl:text>
        <xsl:value-of select="$local-class-name"/><xsl:text>):
            raise MpSchemaError(f"{</xsl:text>
                <xsl:value-of select="translate(LocalName,'.','_')"/><xsl:text>} must be of type {</xsl:text>
                    <xsl:value-of select="$local-class-name"/><xsl:text>}")
        return cls.local_to_gt_dict[</xsl:text>
        <xsl:value-of select="translate(LocalName,'.','_')"/><xsl:text>]

    gt_to_local_dict: Dict[str, </xsl:text><xsl:value-of select="$local-class-name"/><xsl:text>] = {</xsl:text>
    <xsl:for-each select="$airtable//EnumSymbols/EnumSymbol[(Enum = $enum-id)]">
        <xsl:text>
        "</xsl:text><xsl:value-of select="Symbol"/><xsl:text>": </xsl:text>
        <xsl:value-of select="$local-class-name"/><xsl:text>.</xsl:text>
        <xsl:if test="$enum-name-style = 'Upper'">
            <xsl:value-of select="translate(translate(LocalValue,'-',''),$lcletters, $ucletters)"/>
        </xsl:if>
        <xsl:if test="$enum-name-style ='UpperPython'">
        <xsl:call-template name="upper-python-case">
            <xsl:with-param name="camel-case-text" select="translate(LocalValue,'-','')" />
        </xsl:call-template>
        </xsl:if>
    <xsl:text>,</xsl:text>
    </xsl:for-each>
    <xsl:text>
    }

    local_to_gt_dict: Dict[</xsl:text><xsl:value-of select="$local-class-name"/><xsl:text>, str] = {
        </xsl:text>
    <xsl:for-each select="$airtable//EnumSymbols/EnumSymbol[(Enum = $enum-id)]">
    <xsl:value-of select="$local-class-name"/><xsl:text>.</xsl:text>
    <xsl:if test="$enum-name-style = 'Upper'">
        <xsl:value-of select="translate(translate(LocalValue,'-',''),$lcletters, $ucletters)"/>
    </xsl:if>
    <xsl:if test="$enum-name-style ='UpperPython'">
    <xsl:call-template name="upper-python-case">
        <xsl:with-param name="camel-case-text" select="translate(LocalValue,'-','')" />
    </xsl:call-template>
    </xsl:if>
    <xsl:text>: "</xsl:text>
    <xsl:value-of select="Symbol"/><xsl:text>",
        </xsl:text>
    </xsl:for-each>
    <xsl:text>#
    }
</xsl:text>


                        </xsl:element>
                     </FileSetFile>
                </xsl:for-each>

            </FileSetFiles>
        </FileSet>
    </xsl:template>


</xsl:stylesheet>
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
    <xsl:include href="GnfCommon.xslt"/>

    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
        </xsl:copy>
    </xsl:template>

    <xsl:template match="/">
        <FileSet>
            <FileSetFiles>
                <xsl:for-each select="$airtable//ProtocolEnums/ProtocolEnum[(normalize-space(ProtocolName) ='scada')]">
                <xsl:variable name="enum-id" select="Enum"/>
                <xsl:for-each select="$airtable//GtEnums/GtEnum[GtEnumId=$enum-id]">
                    <xsl:variable name="enum-name-style" select="PythonEnumNameStyle" />
                    <xsl:variable name="class-name">
                        <xsl:call-template name="nt-case">
                            <xsl:with-param name="mp-schema-text" select="Alias" />
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="current-version" select="Version" />
                    <xsl:variable name="local-class-name">
                        <xsl:call-template name="nt-case">
                            <xsl:with-param name="mp-schema-text" select="LocalName" />
                        </xsl:call-template>
                    </xsl:variable>

                    <xsl:variable name="overwrite-mode">
                        <xsl:if test="not (Status = 'Pending')">
                        <xsl:text>Never</xsl:text>
                        </xsl:if>
                        <xsl:if test="(Status = 'Pending')">
                        <xsl:text>Always</xsl:text>
                        </xsl:if>
                    </xsl:variable>
                    
                    <FileSetFile>
                                <xsl:element name="RelativePath"><xsl:text>../../../gw_spaceheat/enums/</xsl:text>
                                <xsl:value-of select="translate(LocalName,'.','_')"/><xsl:text>.py</xsl:text></xsl:element>

                    <OverwriteMode><xsl:value-of select="$overwrite-mode"/></OverwriteMode>
                    <xsl:element name="FileContents">


<xsl:text>""" Enum with TypeName </xsl:text>
<xsl:value-of select="AliasRoot"/>
<xsl:text>, Version </xsl:text> 
<xsl:value-of select="Version"/><xsl:text>, Status </xsl:text>
<xsl:value-of select="Status"/>
<xsl:text>"""
from typing import List
from enum import auto
from fastapi_utils.enums import StrEnum


class </xsl:text><xsl:value-of select="$local-class-name"/>
<xsl:text>(StrEnum):
    """
    </xsl:text>
    <xsl:value-of select="normalize-space(Description)"/>
    <xsl:if test="(normalize-space(Url)!='')">
    <xsl:text>
    [More Info](</xsl:text>
    <xsl:value-of select="normalize-space(Url)"/>
    <xsl:text>).</xsl:text>
    </xsl:if>
    <xsl:text>

    Name (EnumSymbol, Version): description
    </xsl:text>
    <xsl:for-each select="$airtable//EnumSymbols/EnumSymbol[(Enum = $enum-id) and (Version &lt;= $current-version) ]">
    <xsl:sort select="Idx" data-type="number"/>

    <xsl:text>
      * </xsl:text>

    <xsl:if test="$enum-name-style = 'Upper'">
        <xsl:value-of select="translate(translate(LocalValue,'-',''),$lcletters, $ucletters)"/>
    </xsl:if>
    <xsl:if test="$enum-name-style ='UpperPython'">
        <xsl:value-of select="LocalValue"/>
    </xsl:if>

       <xsl:text> (</xsl:text>
       <xsl:value-of select="normalize-space(Symbol)"/>
       <xsl:text>, </xsl:text>
       <xsl:value-of select="Version"/>
       <xsl:text>): </xsl:text>
      <xsl:value-of select="normalize-space(Description)"/>

    <xsl:if test="(normalize-space(Url)!='')">
    <xsl:text>. [More Info](</xsl:text>
    <xsl:value-of select="normalize-space(Url)"/>
    <xsl:text>).</xsl:text>
    </xsl:if>

    </xsl:for-each>

    <xsl:text>
    """
    </xsl:text>

<xsl:for-each select="$airtable//EnumSymbols/EnumSymbol[(Enum = $enum-id)]">
<xsl:sort select="Idx" data-type="number"/>
<xsl:if test="$enum-name-style = 'Upper'">
    <xsl:value-of select="translate(translate(LocalValue,'-',''),$lcletters, $ucletters)"/>
</xsl:if>
<xsl:if test="$enum-name-style ='UpperPython'">
    <xsl:value-of select="LocalValue"/>
</xsl:if>

<xsl:text> = auto()
    </xsl:text>
</xsl:for-each>
<xsl:text>
    @classmethod
    def default(cls) -> "</xsl:text>
    <xsl:value-of select="$local-class-name"/>
    <xsl:text>":
        """
        Returns default value </xsl:text>
        <xsl:if test="$enum-name-style = 'Upper'">
            <xsl:value-of select="translate(translate(DefaultEnumValue,'-',''),$lcletters, $ucletters)"/>
        </xsl:if>
        <xsl:if test="$enum-name-style ='UpperPython'">
            <xsl:value-of select="DefaultEnumValue"/>
        </xsl:if>
        <xsl:text>
        """
        return cls.</xsl:text>
        <xsl:if test="$enum-name-style = 'Upper'">
            <xsl:value-of select="translate(translate(DefaultEnumValue,'-',''),$lcletters, $ucletters)"/>
        </xsl:if>
        <xsl:if test="$enum-name-style ='UpperPython'">
            <xsl:value-of select="DefaultEnumValue"/>
        </xsl:if>

    <xsl:text>

    @classmethod
    def values(cls) -> List[str]:
        """
        Returns enum choices
        """
        return [elt.value for elt in cls]
</xsl:text>


                        </xsl:element>
                     </FileSetFile>
                </xsl:for-each>
                </xsl:for-each>

            </FileSetFiles>
        </FileSet>
    </xsl:template>


</xsl:stylesheet>

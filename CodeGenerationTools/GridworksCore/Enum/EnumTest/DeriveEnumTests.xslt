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

                    <xsl:variable name="overwrite-mode">
                        <xsl:if test="not (Status = 'Pending')">
                        <xsl:text>Never</xsl:text>
                        </xsl:if>
                        <xsl:if test="(Status = 'Pending')">
                        <xsl:text>Always</xsl:text>
                        </xsl:if>
                    </xsl:variable>
                
                    <FileSetFile>
                                <xsl:element name="RelativePath"><xsl:text>../../../../tests/enums/test_</xsl:text>
                                <xsl:value-of select="translate(LocalName,'.','_')"/><xsl:text>.py</xsl:text></xsl:element>

                    <OverwriteMode><xsl:value-of select="$overwrite-mode"/></OverwriteMode>
                        <xsl:element name="FileContents">


<xsl:text>"""Tests for schema enum </xsl:text><xsl:value-of select="$enum-alias"/><xsl:text>"""
from enums import </xsl:text><xsl:value-of select="$local-class-name"/><xsl:text>


def test_</xsl:text> <xsl:value-of select="translate(LocalName,'.','_')"/>
    <xsl:text>() -> None:

    assert set(</xsl:text><xsl:value-of select="$local-class-name"/><xsl:text>.values()) == set(
        [
            </xsl:text>
    <xsl:for-each select="$airtable//EnumSymbols/EnumSymbol[(Enum = $enum-id)]">
    <xsl:sort select="Idx"/>
        <xsl:text>"</xsl:text>
        <xsl:if test="$enum-name-style = 'Upper'">
            <xsl:value-of select="translate(translate(LocalValue,'-',''),$lcletters, $ucletters)"/>
        </xsl:if>
        <xsl:if test="$enum-name-style ='UpperPython'">
            <xsl:value-of select="LocalValue"/>
        </xsl:if>

        <xsl:text>",
            </xsl:text>
        </xsl:for-each>
    <xsl:text>
        ]
    )

    assert </xsl:text><xsl:value-of select="$local-class-name"/><xsl:text>.default() == </xsl:text>
    <xsl:value-of select="$local-class-name"/><xsl:text>.</xsl:text>
    <xsl:if test="$enum-name-style = 'Upper'">
        <xsl:value-of select="translate(translate(DefaultEnumValue,'-',''),$lcletters, $ucletters)"/>
    </xsl:if>
    <xsl:if test="$enum-name-style ='UpperPython'">
        <xsl:value-of select="DefaultEnumValue"/>
    </xsl:if>




                        </xsl:element>
                     </FileSetFile>
                </xsl:for-each>
                </xsl:for-each>
            </FileSetFiles>
        </FileSet>
    </xsl:template>


</xsl:stylesheet>

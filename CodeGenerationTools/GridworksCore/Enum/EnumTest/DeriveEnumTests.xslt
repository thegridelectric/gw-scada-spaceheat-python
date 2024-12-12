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
                <xsl:variable name="enum-id" select="GtEnumId"/>
                <xsl:variable name="version" select="EnumVersion"/>
                <xsl:variable name="enum-name" select="EnumName"/>
                <xsl:for-each select="$airtable//GtEnums/GtEnum[GtEnumId=$enum-id]">
                    <xsl:variable name="enum-type" select="EnumType" />
                    <xsl:variable name="local-class-name">
                        <xsl:call-template name="nt-case">
                            <xsl:with-param name="type-name-text" select="LocalName" />
                        </xsl:call-template>
                    </xsl:variable>
                    <FileSetFile>
                                <xsl:element name="RelativePath"><xsl:text>../../../../tests/enums/</xsl:text>
                                <xsl:value-of select="translate(LocalName,'.','_')"/><xsl:text>_test.py</xsl:text></xsl:element>

                        <OverwriteMode>Always</OverwriteMode>
                        <xsl:element name="FileContents">


<xsl:text>"""
Tests for enum </xsl:text><xsl:value-of select="Name"/><xsl:text>.</xsl:text><xsl:value-of select="$version"/>
    <xsl:text> from the GridWorks Type Registry.
"""

from enums import </xsl:text><xsl:value-of select="$local-class-name"/><xsl:text>


def test_</xsl:text> <xsl:value-of select="translate(LocalName,'.','_')"/>
    <xsl:text>() -> None:
    assert set(</xsl:text><xsl:value-of select="$local-class-name"/><xsl:text>.values()) == {</xsl:text>
    <xsl:for-each select="$airtable//EnumSymbols/EnumSymbol[(Enum = $enum-id) and (Version &lt;= $version)]">
    <xsl:sort select="Idx"  data-type="number"/>
        <xsl:choose>
        <xsl:when test="$enum-type = 'Upper'">
                <xsl:text>
        "</xsl:text>
            <xsl:value-of select="translate(translate(LocalValue,'-',''),$lcletters, $ucletters)"/>
             <xsl:text>",</xsl:text>
        </xsl:when>
        <xsl:when test="$enum-type = 'OldSchool'">
        <xsl:text>&#10;        </xsl:text>
            <xsl:value-of select="Symbol"/>
            <xsl:text>,</xsl:text>
        </xsl:when>
        <xsl:otherwise>
        <xsl:text>
        "</xsl:text>
            <xsl:value-of select="LocalValue"/>
             <xsl:text>",</xsl:text>
        </xsl:otherwise>
        </xsl:choose>

        </xsl:for-each>
    <xsl:text>
    }

    assert </xsl:text><xsl:value-of select="$local-class-name"/><xsl:text>.default() == </xsl:text>
    <xsl:value-of select="$local-class-name"/><xsl:text>.</xsl:text>
    <xsl:choose>
    <xsl:when test="$enum-type = 'Upper'">
        <xsl:value-of select="translate(translate(DefaultEnumValue,'-',''),$lcletters, $ucletters)"/>
    </xsl:when>
    <xsl:otherwise>
        <xsl:value-of select="DefaultEnumValue"/>
    </xsl:otherwise>
    </xsl:choose>
    <xsl:text>
    assert </xsl:text><xsl:value-of select="$local-class-name"/><xsl:text>.enum_name() == "</xsl:text>
    <xsl:value-of select="$enum-name"/>
    <xsl:text>"</xsl:text>

    <xsl:if test="$enum-type = 'Upper' or $enum-type = 'UpperPython'">
    <xsl:text>
    assert </xsl:text><xsl:value-of select="$local-class-name"/><xsl:text>.enum_version() == "</xsl:text>
    <xsl:value-of select="$version"/>
    <xsl:text>"</xsl:text>
    </xsl:if>


        <!-- Add newline at EOF for git and pre-commit-->
        <xsl:text>&#10;</xsl:text>


                        </xsl:element>
                     </FileSetFile>
                </xsl:for-each>
                </xsl:for-each>
            </FileSetFiles>
        </FileSet>
    </xsl:template>


</xsl:stylesheet>

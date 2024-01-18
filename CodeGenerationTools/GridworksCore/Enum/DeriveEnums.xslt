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
                <xsl:variable name="enum-version" select="EnumVersion"/>
                <xsl:variable name="enum-name" select="EnumName"/>
                <xsl:variable name="local-name" select="LocalName"/>
                <xsl:for-each select="$airtable//GtEnums/GtEnum[GtEnumId=$enum-id]">
                    <xsl:variable name="enum-name-style" select="PythonEnumNameStyle" />
                    <xsl:variable name="enum-class-name">
                        <xsl:call-template name="nt-case">
                            <xsl:with-param name="type-name-text" select="LocalName" />
                        </xsl:call-template>
                    </xsl:variable>
                    <FileSetFile>
                                <xsl:element name="RelativePath"><xsl:text>../../../gw_spaceheat/enums/</xsl:text>
                                <xsl:value-of select="translate(LocalName,'.','_')"/><xsl:text>.py</xsl:text></xsl:element>

                        <OverwriteMode>Always</OverwriteMode>
                        <xsl:element name="FileContents">


<xsl:text>from enum import auto
from typing import List

from fastapi_utils.enums import StrEnum


class </xsl:text><xsl:value-of select="$enum-class-name"/>
<xsl:text>(StrEnum):
    """
    </xsl:text>
    <!-- Enum description, wrapped, if it exists -->
    <xsl:if test="(normalize-space(Description) != '')">
    <xsl:call-template name="wrap-text">
        <xsl:with-param name="text" select="normalize-space(Description)"/>
        <xsl:with-param name="indent-spaces" select="4"/>
    </xsl:call-template>
    </xsl:if>

    <xsl:text>

    Enum </xsl:text><xsl:value-of select="Name"/><xsl:text> version </xsl:text><xsl:value-of select="$enum-version"/>
    <xsl:text> in the GridWorks Type registry.

    Used by used by multiple Application Shared Languages (ASLs), including but not limited to
    gwproto. For more information:
      - [ASLs](https://gridworks-type-registry.readthedocs.io/en/latest/)
      - [Global Authority](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#</xsl:text>
    <xsl:value-of select="translate($enum-name,'.','')"/>
    <xsl:text>)</xsl:text>

    <xsl:if test="(normalize-space(Url)!='')">
    <xsl:text>
      - [More Info](</xsl:text>
    <xsl:value-of select="normalize-space(Url)"/>
    <xsl:text>)</xsl:text>
    </xsl:if>
    <xsl:text>

    Values (with symbols in parens):</xsl:text>
    <xsl:for-each select="$airtable//EnumSymbols/EnumSymbol[(Enum = $enum-id)  and (Version &lt;= $enum-version)]">
    <xsl:sort select="Idx" data-type="number"/>
    <xsl:text>
      - </xsl:text>
      <xsl:value-of select="LocalValue"/><xsl:text> (</xsl:text>
     <xsl:value-of select="Symbol"/><xsl:text>)</xsl:text>

    <xsl:if test="(normalize-space(Description)!='') or (normalize-space(Url)!='')">
    <xsl:text>: </xsl:text>
    </xsl:if>
    <xsl:variable name="first-line-indent">
        <xsl:value-of select="8 + string-length(LocalValue)" />
    </xsl:variable>

    <xsl:call-template name="wrap-text">
        <xsl:with-param name="text" select="normalize-space(Description)" />
        <xsl:with-param name="indent-spaces" select="8"/>
        <xsl:with-param name="first-line-shorter-by" select="$first-line-indent"/>
     </xsl:call-template>

    <xsl:if test="(normalize-space(Url)!='')">
    <xsl:text> [More Info](</xsl:text>
    <xsl:value-of select="normalize-space(Url)"/>
    <xsl:text>).</xsl:text>
    </xsl:if>

    </xsl:for-each>

    <xsl:text>
    """

</xsl:text>

<xsl:for-each select="$airtable//EnumSymbols/EnumSymbol[(Enum = $enum-id)  and (Version &lt;= $enum-version)]">
<xsl:sort select="Idx" data-type="number"/>
 <xsl:call-template name="insert-spaces">
    <xsl:with-param name="count" select="4"/>
</xsl:call-template>
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
    <xsl:value-of select="$enum-class-name"/>
    <xsl:text>":
        """
        Returns default value (in this case </xsl:text>
        <xsl:if test="$enum-name-style = 'Upper'">
            <xsl:value-of select="translate(translate(DefaultEnumValue,'-',''),$lcletters, $ucletters)"/>
        </xsl:if>
        <xsl:if test="$enum-name-style ='UpperPython'">
            <xsl:value-of select="DefaultEnumValue"/>
        </xsl:if>
        <xsl:text>)
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

    @classmethod
    def version(cls, value: str) -> str:
        """
        Returns the version of an enum value.

        Once a value belongs to one version of the enum, it belongs
        to all future versions.

        Args:
            value (str): The candidate enum value.

        Raises:
            ValueError: If value is not one of the enum values.

        Returns:
            str: The earliest version of the enum containing value.
        """
        if not isinstance(value, str):
            raise ValueError(f"This method applies to strings, not enums")
        if value not in value_to_version.keys():
            raise ValueError(f"Unknown enum value: {value}")
        return value_to_version[value]

    @classmethod
    def enum_name(cls) -> str:
        """
        The name in the GridWorks Type Registry (</xsl:text><xsl:value-of select="$enum-name"/><xsl:text>)
        """
        return "</xsl:text>
    <xsl:value-of select="$enum-name"/>
    <xsl:text>"

    @classmethod
    def enum_version(cls) -> str:
        """
        The version in the GridWorks Type Registry (</xsl:text><xsl:value-of select="$enum-version"/><xsl:text>)
        """
        return "</xsl:text>
    <xsl:value-of select="$enum-version"/>
    <xsl:text>"

    @classmethod
    def symbol_to_value(cls, symbol: str) -> str:
        """
        Given the symbol sent in a serialized message, returns the encoded enum.

        Args:
            symbol (str): The candidate symbol.

        Returns:
            str: The encoded value associated to that symbol. If the symbol is not
            recognized - which could happen if the actor making the symbol is using
            a later version of this enum, returns the default value of "</xsl:text>
            <xsl:value-of select="DefaultEnumValue"/><xsl:text>".
        """
        if symbol not in symbol_to_value.keys():
            return cls.default().value
        return symbol_to_value[symbol]

    @classmethod
    def value_to_symbol(cls, value: str) -> str:
        """
        Provides the encoding symbol for a </xsl:text><xsl:value-of select="$enum-class-name"/>
        <xsl:text> enum to send in seriliazed messages.

        Args:
            symbol (str): The candidate value.

        Returns:
            str: The symbol encoding that value. If the value is not recognized -
            which could happen if the actor making the message used a later version
            of this enum than the actor decoding the message, returns the default
            symbol of "</xsl:text>
            <xsl:value-of select="DefaultSymbol"/><xsl:text>".
        """
        if value not in value_to_symbol.keys():
            return value_to_symbol[cls.default().value]
        return value_to_symbol[value]

    @classmethod
    def symbols(cls) -> List[str]:
        """
        Returns a list of the enum symbols
        """
        return [</xsl:text>
<xsl:for-each select="$airtable//EnumSymbols/EnumSymbol[(Enum = $enum-id) and (Version &lt;= $enum-version)]">
<xsl:sort select="Idx" data-type="number"/>
        <xsl:text>
            "</xsl:text><xsl:value-of select="Symbol"/><xsl:text>",</xsl:text>

</xsl:for-each>
        <xsl:text>
        ]


symbol_to_value = {</xsl:text>
<xsl:for-each select="$airtable//EnumSymbols/EnumSymbol[(Enum = $enum-id) and (Version &lt;= $enum-version)]">
<xsl:sort select="Idx" data-type="number"/>
    <xsl:text>
    "</xsl:text><xsl:value-of select="Symbol"/><xsl:text>": "</xsl:text>
    <xsl:if test="$enum-name-style = 'Upper'">
        <xsl:value-of select="translate(translate(LocalValue,'-',''),$lcletters, $ucletters)"/>
    </xsl:if>
    <xsl:if test="$enum-name-style ='UpperPython'">
        <xsl:value-of select="LocalValue"/>
    </xsl:if>
<xsl:text>",</xsl:text>
</xsl:for-each>
<xsl:text>
}

value_to_symbol = {value: key for key, value in symbol_to_value.items()}

value_to_version = {</xsl:text>
<xsl:for-each select="$airtable//EnumSymbols/EnumSymbol[(Enum = $enum-id) and (Version &lt;= $enum-version)]">
<xsl:sort select="Idx" data-type="number"/>
    <xsl:text>
    "</xsl:text>
    <xsl:if test="$enum-name-style = 'Upper'">
        <xsl:value-of select="translate(translate(LocalValue,'-',''),$lcletters, $ucletters)"/>
    </xsl:if>
    <xsl:if test="$enum-name-style ='UpperPython'">
        <xsl:value-of select="LocalValue"/>
    </xsl:if>
<xsl:text>": "</xsl:text> <xsl:value-of select="Version"/><xsl:text>",</xsl:text>
</xsl:for-each>
<xsl:text>
}</xsl:text>

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

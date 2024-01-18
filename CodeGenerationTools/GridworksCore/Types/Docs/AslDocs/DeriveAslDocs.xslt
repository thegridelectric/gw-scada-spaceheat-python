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
                <xsl:for-each select="$airtable//ProtocolTypes/ProtocolType[(normalize-space(ProtocolName) ='scada')]">
                <xsl:variable name="versioned-type-id" select="VersionedType"/>
                <xsl:for-each select="$airtable//VersionedTypes/VersionedType[(VersionedTypeId = $versioned-type-id)  and (Status = 'Active' or Status = 'Pending') and (ProtocolCategory = 'Json' or ProtocolCategory = 'GwAlgoSerial')]">
                <xsl:variable name="type-name" select="TypeName"/>
                <xsl:variable name="versioned-type-name" select="VersionedTypeName"/>
                <xsl:variable name="python-class-name">
                    <xsl:if test="(normalize-space(PythonClassName) ='')">
                    <xsl:call-template name="nt-case">
                        <xsl:with-param name="type-name-text" select="TypeName" />
                    </xsl:call-template>
                    </xsl:if>
                    <xsl:if test="(normalize-space(PythonClassName) != '')">
                    <xsl:value-of select="normalize-space(PythonClassName)" />
                    </xsl:if>
                </xsl:variable>
                <xsl:variable name="overwrite-mode">

                    <xsl:if test="not (Status = 'Pending')">
                    <xsl:text>Always</xsl:text>
                    </xsl:if>
                    <xsl:if test="(Status = 'Pending')">
                    <xsl:text>Always</xsl:text>
                    </xsl:if>
                    </xsl:variable>
                <FileSetFile>
                            <xsl:element name="RelativePath"><xsl:text>../../../../../docs/asls/json/</xsl:text>
                            <xsl:value-of select="translate($type-name,'.','-')"/><xsl:text>.json</xsl:text></xsl:element>

                    <OverwriteMode><xsl:value-of select="$overwrite-mode"/></OverwriteMode>
                    <xsl:element name="FileContents">

<xsl:text>{
  "gtr_asl": "001",
  "type_name": "</xsl:text><xsl:value-of select="$type-name"/><xsl:text>",
  "version": "</xsl:text><xsl:value-of select="Version"/><xsl:text>",
  "owner": "gridworks@gridworks-consulting.com",
  "description": "</xsl:text><xsl:value-of select="Title"/>
    <xsl:if test="normalize-space(Description) !=''">
    <xsl:text>. </xsl:text>
    <xsl:value-of select="normalize-space(Description)"/>
    </xsl:if><xsl:text>",</xsl:text>

    <xsl:if test="normalize-space(Url) !=''">
    <xsl:text>
  "url": "</xsl:text>
    <xsl:value-of select="normalize-space(Url)"/>
    <xsl:text>",</xsl:text>
    </xsl:if>
    <xsl:text>
  "properties": {</xsl:text>

      <xsl:for-each select="$airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id)]">
      <xsl:sort select="Idx" data-type="number"/>
      <xsl:text>
    "</xsl:text><xsl:value-of select="Value"/>
         <xsl:if test="not(normalize-space(SubTypeDataClass) = '') and not(IsList='true')">
        <xsl:text>Id</xsl:text>
        </xsl:if>

        <xsl:text>": {
      "type": "</xsl:text>
        <xsl:choose>
        <xsl:when test="(normalize-space(SubTypeDataClass) = '') and not( IsList = 'true')">
        <xsl:call-template name="gwapi-type">
            <xsl:with-param name="gw-type" select="TypeInPayload"/>
        </xsl:call-template>
        <xsl:text>",</xsl:text>
        </xsl:when>
        <xsl:when test="not(normalize-space(SubTypeDataClass) = '') and not(IsList='true')">
            <xsl:text>string",</xsl:text>

        </xsl:when>

        <xsl:when test="(IsList = 'true')">
        <xsl:text>array",
      "items": {
        "type": "</xsl:text>
        <xsl:call-template name="gwapi-type">
            <xsl:with-param name="gw-type" select="TypeInPayload"/>
        </xsl:call-template>
        <xsl:text>"
      },</xsl:text>
        </xsl:when>
        <xsl:otherwise></xsl:otherwise>
        </xsl:choose>

        <xsl:choose>

        <xsl:when test="normalize-space(Format) !=''">
        <xsl:text>
      "format": "</xsl:text>
        <xsl:value-of select="normalize-space(Format)"/>
         <xsl:text>",
      "title": "</xsl:text>
            <xsl:value-of select="Title"/><xsl:text>",</xsl:text>
        </xsl:when>

         <xsl:when test="not(normalize-space(SubTypeDataClass) = '') and not(IsList='true')">
         <xsl:text>
      "format": "UuidCanonicalTextual",
      "title": "Unique identifier for </xsl:text>
            <xsl:value-of select="SubTypeDataClass"/>
            <xsl:text> object articulated by the </xsl:text>
            <xsl:value-of select="VersionedSubTypeName"/>
            <xsl:text> type.",</xsl:text>
         </xsl:when>
         <xsl:otherwise></xsl:otherwise>
         </xsl:choose>



        <xsl:if test="normalize-space(Description) !=''">
        <xsl:text>
      "description": "</xsl:text><xsl:value-of select="normalize-space(Description)"/><xsl:text>",</xsl:text>
        </xsl:if>

        <xsl:text>
      "required": </xsl:text>

        <xsl:if test="IsRequired='true'">
        <xsl:text>true</xsl:text>
        </xsl:if>
        <xsl:if test="not(IsRequired='true')">
        <xsl:text>false</xsl:text>
        </xsl:if>

        <xsl:text>
    },</xsl:text>

      </xsl:for-each>
      <xsl:text>
    "TypeName": {
      "type": "string",
      "value": "</xsl:text><xsl:value-of select="TypeName"/><xsl:text>",
      "title": "The type name"
    },
    "Version": {
      "type": "string",
      "title": "The type version",
      "default": "</xsl:text><xsl:value-of select="Version"/><xsl:text>",
      "required": true
    }
  }</xsl:text>

    <xsl:if test="count($airtable//TypeAxioms/TypeAxiom[(normalize-space(VersionedTypeName)=$versioned-type-name)]) > 0">
    <xsl:text>,
  "axioms": {</xsl:text>
    <xsl:for-each select="$airtable//TypeAxioms/TypeAxiom[(normalize-space(VersionedTypeName)=$versioned-type-name)]">
    <xsl:sort select="AxiomNumber" data-type="number"/>
    <xsl:text>
    "Axiom</xsl:text><xsl:value-of select="AxiomNumber"/><xsl:text>": {
      "title": "</xsl:text>
            <xsl:value-of select="Title"/><xsl:text>",
      "description": "</xsl:text>
            <xsl:value-of select="normalize-space(Description)"/><xsl:text>"</xsl:text>
            <xsl:if test="normalize-space(Url)!=''">
            <xsl:text>,
      "url": "</xsl:text><xsl:value-of select="normalize-space(Url)"/><xsl:text>"</xsl:text>
            </xsl:if>
            <xsl:text>
    }</xsl:text>

    <xsl:if test="position() != count($airtable//TypeAxioms/TypeAxiom[(normalize-space(VersionedTypeName)=$versioned-type-name)])">
    <xsl:text>,</xsl:text>
    </xsl:if>
    </xsl:for-each>

    <xsl:text>
  }</xsl:text>
    </xsl:if>

    <xsl:if test="normalize-space(Example) !=''">
    <xsl:text>,
  "example": </xsl:text>
    <xsl:value-of select="Example"/>

    </xsl:if>
        <xsl:if test="count(PropertyFormatsUsed)>0">
    <xsl:text>,
  "formats": {</xsl:text>
    <xsl:for-each select="$airtable//PropertyFormats/PropertyFormat[(normalize-space(Name) !='')  and (count(TypesThatUse[text()=$versioned-type-id])>0)]">
    <xsl:text>
    "</xsl:text><xsl:value-of select="Name"/><xsl:text>": {
      "type": "string",
      "description": "</xsl:text>
            <xsl:value-of select="normalize-space(Description)"/>
            <xsl:text>",
      "example": "</xsl:text>
            <xsl:value-of select="Example"/>
            <xsl:text>"
    }</xsl:text>
        <xsl:if test="position() != count($airtable//PropertyFormats/PropertyFormat[(normalize-space(Name) !='')  and (count(TypesThatUse[text()=$versioned-type-id])>0)])">
        <xsl:text>,</xsl:text>
        </xsl:if>
    </xsl:for-each>
    <xsl:text>
  }</xsl:text>
    </xsl:if>


    <xsl:text>
}
</xsl:text>


                        </xsl:element>
                     </FileSetFile>
                </xsl:for-each>
                </xsl:for-each>
            </FileSetFiles>
        </FileSet>
    </xsl:template>



</xsl:stylesheet>

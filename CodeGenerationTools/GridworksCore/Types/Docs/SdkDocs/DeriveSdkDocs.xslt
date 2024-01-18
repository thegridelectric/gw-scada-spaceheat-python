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
                <xsl:variable name="versioned-type-name" select="VersionedTypeName"/>
                 <xsl:variable name="type-name" select="TypeName"/>
                <xsl:variable name="class-name">
                    <xsl:call-template name="nt-case">
                        <xsl:with-param name="type-name-text" select="$type-name" />
                    </xsl:call-template>
                </xsl:variable>
                <xsl:variable name="version" select="Version"/>
                <xsl:variable name="overwrite-mode">

                    <xsl:if test="not (Status = 'Pending')">
                    <xsl:text>Always</xsl:text>
                    </xsl:if>
                    <xsl:if test="(Status = 'Pending')">
                    <xsl:text>Always</xsl:text>
                    </xsl:if>
                    </xsl:variable>
                <FileSetFile>
                            <xsl:element name="RelativePath"><xsl:text>../../../../../docs/types/</xsl:text>
                            <xsl:value-of select="translate($type-name,'.','-')"/><xsl:text>.rst</xsl:text></xsl:element>

                    <OverwriteMode><xsl:value-of select="$overwrite-mode"/></OverwriteMode>
                    <xsl:element name="FileContents">

<xsl:value-of select="$class-name"/><xsl:text>
==========================
Python pydantic class corresponding to json type `</xsl:text>
<xsl:value-of select="$type-name"/><xsl:text>`, version `</xsl:text>
<xsl:value-of select="Version"/><xsl:text>`.

.. autoclass:: gwstypes.</xsl:text><xsl:value-of select="$class-name"/><xsl:text>
    :members:</xsl:text>
<xsl:for-each select="$airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id)]">
 <xsl:sort select="Idx" data-type="number"/>
<xsl:text>

**</xsl:text>
<xsl:value-of select="Value"/>
  <xsl:if test="not(normalize-space(SubTypeDataClass) = '') and not(IsList='true')">
        <xsl:text>Id</xsl:text>
        </xsl:if>

<xsl:text>**:
    - Description: </xsl:text>
    <xsl:if test="normalize-space(Title) !=''">
    <xsl:value-of select="Title"/>
     <xsl:text>. </xsl:text>
    </xsl:if>
    <xsl:if test="normalize-space(Description) !=''">
    <xsl:value-of select="Description"/>
    </xsl:if>

     <xsl:choose>
     <xsl:when test="normalize-space(PrimitiveType) !='' and normalize-space(Format) != ''">
     <xsl:text>
    - Format: </xsl:text><xsl:value-of select="Format"/>
     </xsl:when>
     <xsl:when test="not(normalize-space(SubTypeDataClass) = '') and not(IsList='true')">
     <xsl:text>
    - Format: UuidCanonicalTextual</xsl:text>
     </xsl:when>
     <xsl:otherwise></xsl:otherwise>
     </xsl:choose>
</xsl:for-each>
<xsl:text>

**TypeName**:
    - Description: All GridWorks Versioned Types have a fixed TypeName, which is a string of lowercase alphanumeric words separated by periods, most significant word (on the left) starting with an alphabet character, and final word NOT all Hindu-Arabic numerals.

**Version**:
    - Description: All GridWorks Versioned Types have a fixed version, which is a string of three Hindu-Arabic numerals.

</xsl:text>
<xsl:for-each select="$airtable//PropertyFormats/PropertyFormat[(normalize-space(Name) !='')  and (count(TypesThatUse[text()=$versioned-type-id])>0)]">

<xsl:text>

.. autoclass:: gwtypes.</xsl:text>
<xsl:value-of select="translate($type-name,'.','_')"/>
<xsl:text>.check_is_</xsl:text>
<xsl:call-template name="python-case">
    <xsl:with-param name="camel-case-text" select="Name"  />
</xsl:call-template><xsl:text>
    :members:
</xsl:text>

</xsl:for-each>

<xsl:text>

.. autoclass:: gwproto.types.</xsl:text>
<xsl:value-of select="$class-name"/><xsl:text>_Maker
    :members:

</xsl:text>


                        </xsl:element>
                     </FileSetFile>
                </xsl:for-each>
                </xsl:for-each>
            </FileSetFiles>
        </FileSet>
    </xsl:template>



</xsl:stylesheet>

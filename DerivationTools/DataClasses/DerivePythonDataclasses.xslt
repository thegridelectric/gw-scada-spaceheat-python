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
    <xsl:include href="GwCommon.xslt"/>

    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
        </xsl:copy>
    </xsl:template>

    <xsl:template match="/">
        <FileSet>
            <FileSetFiles>
                <xsl:for-each select="$airtable//GwEntities/GwEntity[(normalize-space(IsNotDataClass) != 'true']">
                    <xsl:variable name="entity" select="." />
                    <xsl:variable name="od" select="$odxml//ObjectDefs/ObjectDef[Name=$entity/Name]"/>
                    <xsl:variable name="lower-name" select="translate(Name, $ucletters, $lcletters)" />
                    <xsl:variable name="python-odname">
                        <xsl:call-template name="python-case"><xsl:with-param name="camel-case-text" select="Name"  /></xsl:call-template>
                    </xsl:variable>
                    <FileSetFile>
                        <xsl:element name="RelativePath"><xsl:text>../../data_classes/</xsl:text><xsl:value-of select="$python-odname"/><xsl:text>_base.py</xsl:text></xsl:element>
                        <OverwriteMode>Always</OverwriteMode>
                        <xsl:element name="FileContents" ><xsl:text>""" </xsl:text><xsl:value-of select="$od/Name" /><xsl:text> Base Class Definition """
import time
import uuid
from typing import Optional
from abc import ABC, abstractproperty
from gw.mixin import StreamlinedSerializerMixin

</xsl:text>

</xsl:element>
</FileSetFile>
</xsl:for-each>
</FileSetFiles>
</FileSet>
</xsl:template>

</xsl:stylesheet>
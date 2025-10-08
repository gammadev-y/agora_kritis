# Law Type Mapping Reference

Quick reference for Portuguese legal document types and their database IDs.

## Primary Legislation

| Portuguese Name | Database ID | English |
|----------------|-------------|---------|
| Lei | LEI | Law |
| Lei Constitucional | LEI_CONSTITUCIONAL | Constitutional Law |
| Lei Orgânica | LEI_ORGANICA | Organic Law |
| Decreto-Lei | DECRETO_LEI | Decree-Law |

## Decrees

| Portuguese Name | Database ID | English |
|----------------|-------------|---------|
| Decreto | DECRETO | Decree |
| Decreto Legislativo Regional | DECRETO_LEGISLATIVO_REGIONAL | Regional Legislative Decree |
| Decreto Regional | DECRETO_REGIONAL | Regional Decree |
| Decreto Regulamentar | DECRETO_REGULAMENTAR | Regulatory Decree |
| Decreto Regulamentar Regional | DECRETO_REGULAMENTAR_REGIONAL | Regional Regulatory Decree |
| Decreto do Governo | DECRETO_GOVERNO | Government Decree |
| Decreto do Presidente da República | DECRETO_PR | Presidential Decree |
| Decreto de Aprovação da Constituição | DECRETO_APROVACAO_CONSTITUICAO | Constitutional Approval Decree |

## Administrative Acts

| Portuguese Name | Database ID | English |
|----------------|-------------|---------|
| Portaria | PORTARIA | Ordinance |
| Despacho | DESPACHO | Order/Dispatch |
| Despacho Conjunto | DESPACHO_CONJUNTO | Joint Order |
| Despacho Normativo | DESPACHO_NORMATIVO | Normative Order |
| Aviso | AVISO | Notice |
| Aviso do Banco de Portugal | AVISO_BP | Bank of Portugal Notice |
| Edital | EDITAL | Edict |
| Alvará | ALVARA | Permit/Charter |

## Resolutions

| Portuguese Name | Database ID | English |
|----------------|-------------|---------|
| Resolução | RESOLUCAO | Resolution |
| Resolução da Assembleia da República | RESOLUCAO_AR | Assembly Resolution |
| Resolução do Conselho de Ministros | RESOLUCAO_CM | Council of Ministers Resolution |

## Jurisprudence

| Portuguese Name | Database ID | English |
|----------------|-------------|---------|
| Acórdão | ACORDAO | Ruling |
| Acórdão do Tribunal Constitucional | ACORDAO_TC | Constitutional Court Ruling |
| Acórdão do Supremo Tribunal de Justiça | ACORDAO_STJ | Supreme Court Ruling |
| Acórdão do Supremo Tribunal Administrativo | ACORDAO_STA | Administrative Court Ruling |
| Acórdão do Tribunal de Contas | ACORDAO_T_CONTAS | Court of Auditors Ruling |
| Acórdão doutrinário | ACORDAO_DOUTRINARIO | Doctrinal Ruling |
| Assento | ASSENTO | Jurisprudential Ruling |

## Constitutional Documents

| Portuguese Name | Database ID | English |
|----------------|-------------|---------|
| Constituição | CONSTITUTION | Constitution |
| Carta Constitucional | CARTA_CONSTITUCIONAL | Constitutional Charter |
| Revisão Constitucional | CONSTITUTIONAL_REVISION | Constitutional Revision |

## International

| Portuguese Name | Database ID | English |
|----------------|-------------|---------|
| Tratado | TRATADO | Treaty |
| Convenção | CONVENCAO | Convention |
| Acordo | ACORDO | Agreement |
| Protocolo | PROTOCOLO | Protocol |
| Carta de Adesão | CARTA_ADESAO | Letter of Accession |
| Carta de Ratificação | CARTA_RATIFICACAO | Letter of Ratification |

## Regulatory & Organizational

| Portuguese Name | Database ID | English |
|----------------|-------------|---------|
| Regulamento | REGULAMENTO | Regulation |
| Regimento | REGIMENTO | Standing Orders |
| Instrução | INSTRUCAO | Instruction |
| Circular | CIRCULAR | Circular |

## Other Administrative

| Portuguese Name | Database ID | English |
|----------------|-------------|---------|
| Deliberação | DELIBERACAO | Deliberation |
| Decisão | DECISAO | Decision |
| Declaração | DECLARACAO | Declaration |
| Declaração de Retificação | DECLARACAO_RETIFICACAO | Rectification Statement |
| Errata | ERRATA | Erratum |
| Comunicação | COMUNICACAO | Communication |
| Anúncio | ANUNCIO | Announcement |
| Contrato | CONTRATO | Contract |
| Aditamento | ADITAMENTO | Addendum |
| Alteração | ALTERACAO | Alteration |

## Parliamentary & Governmental

| Portuguese Name | Database ID | English |
|----------------|-------------|---------|
| Moção | MOCAO | Motion |
| Moção de Confiança | MOCAO_CONFIANCA | Motion of Confidence |
| Moção de Censura | MOCAO_CENSURA | Motion of Censure |
| Parecer | PARECER | Opinion/Report |
| Programa | PROGRAMA | Program |

## Reference Materials

| Portuguese Name | Database ID | English |
|----------------|-------------|---------|
| Lista | LISTA | List |
| Mapa | MAPA | Map/Chart |
| Mapa Oficial | MAPA_OFICIAL | Official Map |

## Fallback

| Database ID | Usage |
|------------|-------|
| OTHER | Default for unknown/unrecognized document types |

---

## Notes

- All mappings are **case-insensitive**
- Mapping is **static** (no database lookups needed)
- Unknown types automatically fallback to `OTHER`
- Total: **68 distinct law types** supported

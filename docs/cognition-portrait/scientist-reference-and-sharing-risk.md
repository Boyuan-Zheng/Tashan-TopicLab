# Scientist References, Share Cards, and Risk Boundaries

## 1. Scope

This document records product-facing risk boundaries for using scientist references in TopicLab portrait products.

It is not formal legal advice. It is a product design and implementation guideline based on public source review.

The goal is to maximize:

- fun
- recognizability
- shareability

while minimizing:

- copyright risk
- portrait / personality-right risk
- false endorsement risk
- privacy and re-identification risk

## 2. Core Conclusion

Using only deceased scientists does **not** automatically eliminate risk.

Why:

- a deceased person's name, portrait, reputation, and related interests may still be protected
- the image of that scientist may still be copyrighted even if the scientist is long dead
- some jurisdictions recognize postmortem commercial personality rights
- a share card can still create endorsement or misleading association risk

Therefore the safest product rule is:

- use original TopicLab portrait types as the primary identity
- treat real scientists as optional historical references
- avoid using real scientist photos as the main share-card visual

## 3. Risk Categories

### 3.1 Portrait / Personality / Related Civil Interests

In China, the Civil Code protects portrait and related personality interests. For deceased persons, close relatives may defend certain interests.

Product implication:

- do not assume death means free commercial use
- especially avoid using a real person's recognizable image as a promotional hero asset

### 3.2 Copyright in Images

Even if a scientist is deceased, the photograph, painting, or derived illustration may still be protected by copyright.

Product implication:

- the person and the image are separate rights questions
- an old famous face can still sit inside a protected photo archive

### 3.3 Postmortem Commercial Personality Rights in Other Jurisdictions

If TopicLab content can circulate internationally, some jurisdictions recognize postmortem commercial rights. California is one example for certain deceased personalities.

Product implication:

- international share surfaces should not assume one-country rules are enough

### 3.4 False Endorsement / Misleading Association

If a card reads like a real scientist is endorsing TopicLab, endorsing a user, or authorizing the product, risk increases even without a direct copyright dispute.

Product implication:

- never use endorsement-like language
- never imply official affiliation, authorization, or sponsorship

## 4. Safe Product Policy

### 4.1 Primary Rule

The main result card should use:

- TopicLab-original type name
- TopicLab-original visual identity
- TopicLab-written interpretation text

The card should not depend on a real scientist's name or image to function.

### 4.2 Scientist Reference Rule

Scientist references are allowed only as:

- textual reference points
- historical style comparisons
- optional secondary detail

Recommended labels:

- `历史科学人物参考`
- `研究风格参考`
- `你可能更接近以下历史科学人物的工作气质`

Avoid labels like:

- `你就是某某`
- `当代某某`
- `某某为你代言`

### 4.3 Image Rule

Default rule:

- do not use real scientist photos on the main share card

Preferred visual alternatives:

- original illustration
- abstract badge
- symbolic research objects
- diagrammatic poster
- lab-material collage without identifiable likeness

If TopicLab later needs real historical images, require all of the following:

- clear provenance
- explicit rights assessment
- confirmation that the source is suitable for the intended use
- no misleading sponsorship or endorsement framing

## 5. Image Source Policy

### 5.1 Preferred Sources

If real historical images are ever used, prefer:

- `CC0`
- clear `Public Domain`
- archival items with explicit low-risk rights statements

### 5.2 Important Limitation

Even open-access institutions often warn that open access does not remove every possible third-party restriction.

So product policy should remain:

- open image source is helpful
- open image source is not the only question

### 5.3 Default Implementation Recommendation

For V1:

- do not ship real scientist images in share cards
- only ship text references and original artwork

This is the most robust default.

## 6. Share Surface Policy

### 6.1 Light Share Card

Allowed:

- original type name
- short tagline
- high-level descriptive copy
- original artwork

Not allowed:

- real name
- institution
- mentor
- current employer
- precise research topic
- vulnerability-heavy private content

### 6.2 Rich De-identified Card

Allowed:

- high-level field category
- cognitive style summary
- motivation summary
- collaboration style summary
- development path summary
- optional historical scientist reference text

Must remove or generalize:

- full name
- school, lab, institute, company
- narrow topic labels that identify the user
- unpublished project details
- emotionally sensitive raw material
- combinations of signals that make the person easy to identify

## 7. Recommended Wording Patterns

### 7.1 Good Patterns

- `你的研究人格类型是……`
- `历史科学人物参考`
- `你在研究风格上更接近……`
- `以下人物仅作为研究气质参考，并非学术评价或人格诊断`

### 7.2 Bad Patterns

- `你就是爱因斯坦`
- `某某同款人格`
- `某某会支持你的研究方式`
- `官方认证你最像某某`

## 8. Product Decision For V1

V1 should adopt the following constraints:

- real scientists are not the main type
- real scientists are optional text references only
- real scientist photos are excluded from share cards
- main share card uses original TopicLab visual assets
- full portrait stays private by default
- rich share card must pass de-identification rules

## 9. External Sources Reviewed

- PRC Civil Code personality-interest and portrait-right provisions
- PRC Copyright Law term rules
- FTC endorsement guidance
- California postmortem publicity statute
- Library of Congress rights guidance
- Smithsonian Open Access FAQ

Reference links:

- PRC Civil Code overview and text references:
  - <https://www.yantian.gov.cn/ytfl/gkmlpt/content/8/8945/post_8945245.html>
  - <https://fgw.sh.gov.cn/cmsres/98/98301d29f26f462dba5ac280b2180c79/0398f64d92c81f5982924d8e107e67c9.pdf>
- PRC Copyright Law:
  - <https://zjjcmspublic.oss-cn-hangzhou-zwynet-d01-a.internet.cloud.zj.gov.cn/jcms_files/jcms1/web2328/site/attach/0/951962c09aee41b581cdd3055ea7bdb9.pdf>
- FTC:
  - <https://www.ftc.gov/business-guidance/resources/advertising-faqs-guide-small-business>
  - <https://www.ftc.gov/business-guidance/resources/ftcs-endorsement-guides-what-people-are-asking>
- California CIV 3344.1:
  - <https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=CIV&sectionNum=3344.1>
- Library of Congress:
  - <https://www.loc.gov/research-centers/prints-and-photographs/researcher-resources/copyright-and-rights-and-restrictions-information/>
- Smithsonian Open Access:
  - <https://www.si.edu/openaccess/faq>

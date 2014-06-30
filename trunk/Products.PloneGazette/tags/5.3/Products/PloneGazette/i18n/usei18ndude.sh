#!/bin/bash 

i18ndude rebuild-pot --pot plonegazette.pot --create plonegazette ../

i18ndude sync --pot plonegazette.pot plonegazette_*.po;
i18ndude sync --pot plone.pot plone-??.po


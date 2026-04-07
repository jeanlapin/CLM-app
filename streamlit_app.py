from __future__ import annotations

from pathlib import Path
from html import escape
import inspect
import base64
from io import BytesIO
from datetime import datetime, timezone
import json
import re
import hmac
import shutil
import unicodedata
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
import zipfile

import numpy as np
import pandas as pd
import altair as alt
import streamlit as st

REPORTLAB_AVAILABLE = True
REPORTLAB_IMPORT_ERROR = ""
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
except Exception as exc:
    REPORTLAB_AVAILABLE = False
    REPORTLAB_IMPORT_ERROR = str(exc)
    colors = None
    A4 = None
    landscape = None
    ParagraphStyle = None
    getSampleStyleSheet = None
    mm = None
    ImageReader = None
    pdfmetrics = None
    TTFont = None
    PageBreak = None
    Paragraph = None
    SimpleDocTemplate = None
    Spacer = None
    Table = None
    TableStyle = None

PAGE_TITLE = "CLASSIFICATION MANAGEMENT"
APP_SUBTITLE = "Pilotage du portefeuille, gouvernance des risques et supervision multi-société"
PRIMARY_COLOR = "#163A59"
SECONDARY_COLOR = "#5E8FC7"
ACCENT_COLOR = "#DDEAF8"
CARD_BACKGROUND = "#F5F9FE"
LOGO_DATA_URI = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFsAAABbCAYAAAAcNvmZAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAAFxEAABcRAcom8z8AACQuSURBVHhe5V0HeBRl849+n352REEkye5e6FIEqSlb7i70HkhyZa+ELqj0IiCCCgJSLXQBpYsUQRAUsAMiYEEQqUov0qQFCMn8n99sLiR7CQmRAPqf55knIdxt+e288878Zt53Q0LuEJE0/6OWmMTKgqo3FVRXF1F2jRFk54Jw1bVWVNw7RcV5UlBcl0XFRQE1/u08KSquXYLiXCfKroWi7B4ryO5uxRV3s9DohCqi7C5sPtf/K6lWrf09ouKJCFfcqqC4HZKidxU1zxCL1T/eYvfPEW3+TyxW73pJ82wTNX2/qLoB6EVBdl3NArbx74v8//ic5vkV3xNtvhWi3T/HYvVNwHElzd0tXNNd4bJLE6IdJcuXH3iv+Zr+VVK+fMK9sLJQ2VtGUt0NRKunt6R6Z0mKvlFU3cdE1XNZsvquSjb/VcnmS7VYfamS5k2TND1NUvU0UXGTodfADvwN/8+f07xp/D0b1H8Vx8NxRc19XNI8m0XVO0fSPH1Fxd/IEt26bHhk/GO4LvO1/qOlVE39EVHxRAuq3kVQXTNEzbNOsvt3Sjb/SUnzXrVY/WSxZVYfSVYvSZoHQJKkZgf0NcDx//w5fN7q5e9nOZ7VT5LmTbXYkk5Z7P7doupZL6nuWZKqdxdUhyJpzR41X/M/ToRoZ2iY6rbBh0o233ui5vtJ1PRLEbYkiohtTRZ7K7JYfSSpnuuA+XcVD8LD54mwt+Lz4vyipl+RrL4tkt03I1x19whTnPYwTQ8338MdL8XqeB4M1xIrSpqno6jpH0mq55DF5kuWbP5Uyeoji2pYrMhaUCCbNGD9qm6cH9dh86da7L5kSfMcFq36UovmfcFi81QuG930YfM93ZFSrJbDIsY42sBdSHb/T5LNd9ZiTyJWuAcNVgwAnOmaDTAFptfOKWm64W7Sr02y+c9LsUk/i5pntii72z0hu0uY7+2OEVFuVNgiO2tJVm9/i+ZdK2n6FcNVJGUC+M5UXB+uM6J2a/j2q5Lm+05U/S9jnsEkar7X2yqlqsQXFRSHQ9K8H0h2/wGLPemyYcVew10UmD++WRqYYDG5+sli91+RbP5DouZZGK649IhazmLme74tIsQ4K4iKq5dk830p2fx/wTqyWvOtdhX51UzuBVYe2xqu5Zxk9X0jKK4Xw9X4SiEhIXeZ7/+WSHhk/P0lNG91Ixnxbo8I+L473GXkVTNcC9+Tb4eg6cMtsqdW8WqNHzBjUbDSvv09FtmlWaze8ZLNt59ndRti2YIM4W61ug3AOVZPSpOs3oOS6pkiRjntIQm3KBEqqmkPhcp6rGT1TomIbXWQJ0GbPx3kf4rLyKviftx8fxGxrWDlRyyqd5qg6HUfL+jwUNK0+0Q5sbagemZINv8x9mvZuA0p6KLzp5IKDWSIN++4+VHcJwC32Px/Iu0PV1z14ErNGN0UKVWq/v8sSqJqsXqm4ITI/pAY5GTR4THO/KlsqCAHH/P2afrkafUagFv9JyxW7zRRcdolSbvPjNXfk2rV7hFldzWLqk+IsCcdYNdh9V67iHTrC4tx0OPV4+jhpxvTg5Ua00P5Uf5uI3ookz78dBN69JlmVKRGHBWPSiBRvnbOYGAKUp0k2QzAI+ytDklWz5RwJb5mSPnyN8+HizXjy4uKe7Bk9e+LsLfmJ5x5IsRNwxKfjEygJyPjKVx2UAmbl8rE+qh0rI9K3YCWtHuphNVDFtVN4dEOerJWPBWp3oIeqxpHj1VrTkVqtKBiNeMZdDxc4/xmUApS3SRZ4VJ4rjogaK7hYbVaPm3GLF+CDApEkqjpOy02pNxJQREHgC5WqyUJMU6K9fWk7kMm0NCJc2nUu/PpjcnzaPgN6LBJc2nI+Fn08tj3qNfQSfTsgDHk7DyYavt6U+VG7RhgWP8DFRtS4arNKCw6kSya4dODgSk4zUjzNc8eUXX2LiXHFzVjd0NS7Ok6D4pRznhR1b8xuA0/SSag4WeL1mjBlmZ1d6fR0xbQz9v30KFjJ+j4idN05M+TdOR43vXwsRN04Mhx2rP/MG3b9Qdt+Gk7rfz6e5q5eBW9MfkDev6Vt6lR235UsUFbeqJWSypUpQm7l/AYB4+GWzWJAgcj22xFohWUrcNdtHzCQ2YM8yxhsrOWILsXSJr3YnYJC9wHQIZfhbvoNmQCbdyyg1KuXqW/K2lpaXQ1NZWupKRQ8qXLdPb8RTp55izt3neYPvtmEw0eN4satO7L1/Folab8wA0QgoEpKA0kPqLVe0lU3EuKy+4YM4Z5kqLRzUtKqt5fsvoOGwSNJ4gOBdjw0/eVr09PN2pHo6Z+SAePnjDjdtPl8pUrtPP3g7R0zXp+wJUbt+cJ9LGqzdmVwcLNwBSMGolPRGwbEq2+Y4LmfiVUbl7GjOV1BSlpeFRCa0nzfAtSBilr8Ikyg92AqjTpQGOnLaT9h4+ZsSlQgct69e2ZVLXps+xSnqjZ8paHjZjHJLs/RdI8GwQlsUP5G3EnUlSLcqLift9i9V68loYHnyQD7AoG2KPf/ZD+OHjUjEeBSkrKVdr5+wHqP3oqla/XigpXbc4uxUiIgq+5IJQZQy7F+ZJF1T0nwiCtcpeIWk2KCbKjIyrV5njarJnBxlAeOWU+/X7giBmPWyKbt+7gyCU0OpHjfI6JbxHYfC64E8Pd7hBURxepRsKTZmyDRIyKtwuK62PJalRYQDneTLBT01Lp7LkLdODwcf4sRsK+g8dY9x86RgeP/klH/zxFp/86R1eupJi/nqNgUp63/AuKjH+eJ0xcFyIl8zUXjOLBGtSsZPVdEFT3SiHGWee6lCxqbxbV1UVQ3Yeziz7Mmh+wL166RF9u+In6jZpKbfuO4lCu86vvUOdX3qEur71DPYZOpIFvvkdT5i2n737cTn+dPW8+RI6yedtOav3iCI5IHn2mKRWPTLilWSYXlu2tSND0o5LV3SPnBiFN+y9ST0nVZ4hWTyqHNNkcMOvBbxzsv85foHfnf0JVmrSnhys34WEfrhhciKA4yaLpVLZuEsmOLtTmxRE086NVtO/QUbp6NdV8qCDZd/gYjZjyAU+WD1ZsyJPlrQQbanBG3lTRqs8VYlwycDVDHYKnIMgJ3UTNs0Wy+dJQ1jIfyKz5BXvCnI+pTG0f3VW6NhVCyFY9jjkV1mpxHMYhQ0T8btO705QPlnOSlJuc+usczVv2BdX29qQHKjRMnyhvMdjpPSui6tkuxDj6hNZo/rgZ65Aw1VVaUJ2zJM17AWye4auDD5ZZ8wP22fMXaPIHy6h8vdZ071P1qEiNllSMORVDi9WKp6I1WvIkd3fpWCpcrRm16DSQVq/dbD5UkFxMvkSrv91McR1fZlKrSPW4oGsuaOWyGtokrN5kUXF9UFxzlcsCtKT57wu3uuqJqns9Glngq/Myk+cX7KkffsKfB8cRGu1Ag+S1Y8I60q0RJBQsHNnpOzMW04WLyebDZRFkm2s3byVn19foEaTxtwNshJzp3LeoeTaEat7GWXhvUW5RQrC6+ljs3t1cEOCKeO4zeUGAHThuIO1+kD+TSC+PmZ5rwoSY+7sft5G762CDM7kNYAcik3RWcG+4pg8Ij/SUygA7XElUEYxbbL7TsGwjLb99YGc+PiZRnKPX0Im0Y+9+5kxykstXUuibjVsosfOr9Ehlw43cSq7EUCfjx4Viq/esoLoXhKFumQG27HSJivsHSfNdhb8xcyA5aUGDDcVnikclUv9R0zgmvx7YIKs+/nw9s4IPVmqYb7B5ZGXR4M9cV1U3J4OS1ZMqKq6tYpTDmwG2oDi7iorrBHd7cpNjNgfIRgsSbISCABlupJTdR2OmLaQzucTcoHMnz11G0QkvsK8v+jdCP1xTdteVV+UkhwvhztPhiqMnA124dkIhUfMMFlX9yrUqefCXs9P8gj1tAeLsDuwiwpDlmSzJouqckIDgAmh2T09asnpdrrE2OJIer0/gCfWRyk2oWGR8rmAHzinKTi5EoAhStAZC0OZcGUIoiugIFaiwmMSs38nmeNfU4LtFVb8qafowbmMLk1s+bbH5xiEQN8A2fylnzQ/YiLMnzf2YytZJov+UrsPEEUpdiImh+B1lMDyIe8rV4yIBWL3f9h4wHyqLYHJc8dUGqpvUm+P1J2q05KpOdqAESCoePZEJPALwnSLVm9Pj1ZvzT7ggFCXw08gBAv/XgpMljDp8/3qEF5N4Vi86dycJ0S2rh1jU+KZYWsHd/rcC7HPn6Z2ZH/GFhoTJdO9T9en+ig3ZgqH3V2hA/3uqPic2lRq2pb4jptKPv+7mAsL1ZPvu/fTS6OkUYdPZPV2PFzHAMYAuVKUpF5gLPdOULRvZa9WmHSgq/nmKTuxMtVo8x/eG0QLrfqQyPt+YCldrzlGSmN5uYT4HlMHGKgh70nwhxpkYIimJXS027wosi8hL1pj1om8c7PMXLtKHK76m5h0GUM2mHUh1dSOr3p1LalC7pwc1bNOP2vYbSW+9v5h+3LaLUlOv7z72Hz5Oo6cuoMiWz/NIwfDPbqijVomfcC8IDUFY4W+gBlxdB1PPoRNp2OR5NG7WEqYUpn64gjmat2cs5spQl9fGUYtOg6hGXCe2bLgqgB4WbYygoPOhudRYcrJKinH2DRFl51iL1bOe16IwnRoMak6aH7DB5G3fvY8+XPEVT5TgPmYtWc0/oXM//pxWfr2Rtu7Yy8xfamr20QfcxrnzF+m3Pftp3MyPSHN35wIw/Gt2Vs3WrLqoeFQ8fw6uoEbzjtSu32iaPG85rd20lfYdOsYj79LlK1n04qXLTAWgLrpm7Wausya+8CqVq5vEPh1uBjVQrtxkPieWnDCuno1CjHMSIpGFWJVlLBbKeyRi3MCNg43QDRePeuLxk6fpz1Nn6MSpv/gnFH+/kHzJ/LUsgmMcPPInLVz5DT07YCxVatiG3QFARINPwIIzXyf+9kTNFpxZotWiZadBzLls3rqLC815pXNBCSC5+ur7LTRk/GyKSezMIwklObiVzOfmTFzzpolWz05BcawIEWTnelHV90uaByuuggC9nuYH7JshcCs79h6gN99bRDa9BwP4nzJ16JEqTXl4m6MbXCsK00h0YOFJvd/g6AbW+ndkz4HD7HJwDQCba6CZ8dHQ862niap+VFAcP4eIsmu3qLhP8vK2HBx9Tnq7wEYIiJYHkFPoS3F1HUKVGrQ1mnmqxdGTADyTReMBwPIRnejdX6c1635kC81J4LpQjICiwp+TYIQdO3ma3pqxmCdVWDgiG4wuw22509V1VlKdh+FGTomK+6IRXweDndlCzAru+XaAjZtEdPLnyTO0+49DTD6Nn7WU4joOTC+LIcWPz7h+PARYfaN2/WnJ6rXXdVOgcr/Z+AstWPE1T+Qrvv6eR9GVlJzbM37d9Qf1GjaRIxZENqFRiWTJHA7KzhRRcSaHCIrrkrFSNivYuEg4/WI1Wxqxb3r8ey3ujGOgn6gZz2CjGHCrwM5OTp05R4s+/Ybc3YewNcGSATgaeTC8y9dvTSOmzOdJNzvBA9j0yw4aO30hV3vQkwJNeOEV7s7CpI05JTvBg1/17SZq2KYvU8PBFX7j9xBRcaWZrTkANqwEmRQuHIpQCfEvCP9CVZpx4oBhg9iYwX739oENATey6tvN5O72OhsBwkD0tOA+fL2G0RcbfjJ/hQVgrfthK4d2ZWv72RUFDAquAcA17fASLfr0a7qQnD3Ni9opQkfQw8AM9LAZU4Ad9EcuUclOHhbwRTVbPMeFVM3Vjer4elODNn2pYet+HJ9arDonIU83asuW/cfB64MNznnnHwdp6ep1NHvJavrwk68yhizCQfy++LNvacWXG+jbTVs53EL4lVe5cPEyh5K1fb0Y7BBRpYoN2tD42UtytMy9+w/TwLHvcVZ7d6na9N8yddntcMJTsRGFRNj4WB0Hvkmbtu7kJiGznL+YTBPnfkwxCZ35s9BAuJkj2JhN4XPgPvDFF9+YzENr2KR5NOitGcy+oSD7ylszuEZYoUEbuqdsPaqAYTr5g1z7Rs5duEgLVn5Fcc++TNWaPUuaqzvZ9Z5kY+3BPEhdfx/+/zYvjqTXx8+mpWvW0d4DR/IMOkbXsIlzqKTNQ3dbNG7K/Hz9j+aPsYCWxYNHCHdv2XqcqCBExKQKxai4v0JDpg6qNe9I42ctoVNnzpoPQ8mXLtHyL9ZTwvOvGnNE5SZBqTx89mVBdoIKzLBqDAG4i4at+9KCFV/Rjt8P0LebfuGsqv/oaUz2oAqudx/KvvDectfA/v3A9cFG0gALKFvHT/8pW8doA67ZgooGtAa4h3i+BqTPAAx1yIFjp9P6n35lcHKTq1evsjtBNvrYM804Avllx+/mj7EcPHKchk2Yy/49JFzmMDKjHsp8SRyDjXoprg/3nl2LXUpKCm3c8hs9N/AtKlYL/Y/oXQn0Hqb7bEF2nhZkZ3JgcgTYsGycKLLlCzy8Fn/2DS37fD1NX7CSrbpN3xHU9NkBFJ3QmX07aomVGrajkXkEe8KcpVQq1kshpWJ5uCLl5cQgPTnAEIRlgCu5u3Rtuu+p+lSmtp96DZ/MoCF7zE1+3bWP2vcbTc807UBdBo9j12UWUOM//7aHerw+ka34/nL1mNlD6IYwEYogARMeEqYno+Lp+YFvZTt6ESGh/7D/yKn8/cxgC7IzRVCclxD67RFU1ylznI0vgGtGY7qc2Jn8vYZR/1FTadjEuTTozfc5c4v19OSHAx/HYOchGgHF+u785VSpUTt6oFIjjonD0pd2ZCgv+XAw54BkBA/g7tJ16OlG7Wn87KV0+NhJ82GDBH749fFzKP75V9jlwfebBfE0qANwH4jVm7Z/iTw9hpKv5zDy9hiaoa5uQyjhhVeZP8Fnczo/MsvB78zkkBhgc4KDhQKK+5ygOI+ECIrjO1FxH8icQcLP4At4oveWq093lYrlGRZ+DYAv/+I7WrtpGw2fNI8nxrtK2LlanhefHSgeXI/PNsfyABwZInwhsj9MnLkJooNpH66grq+N40zzj0PB1wXLRkECFok+8LU/bKPvf/6Nvt+SVTf8vJ2+++lX/syuPw5RcnL2DCQeApr5S9q8zDwKuAdNTxMU9zFBdm4JERXHIoum/5odN8KWFZnA1gvfDK6497DJNGPRZ8xL9B35LpWv34ruLhlLFeq34QaZvIKdW6UmoAAc58cwBumjubvRB8u+MB82SNDCtnDl1/Ta27MYdDTYF7ScOP0Xk1Sl7F5ObgRjiTbS9V2C7FgZIsS43pQ073eZWT8MY0xQZWsnUZN2/an38Mk0ZvpCHkIgXzr0H011/b05EsHEggmycuN2eYqzbxxsYx7BxAl3Ur15R547iLJnAwOCVQ+IMpDIIBTMS5PP3xU8YFh2hFVnsEU0y/OOQJ5NQoxzSoggu7pLNv9KSzqfbUQjCVT4mWZUx9+bZn20irbt3scE/rLPv2Piv9/IqdSm70j+fxz4nnLw2YizC8Ky09fsoJpSrTnH/fh+bsJgr1nHBjB7yZoCBxsTJFxNxwFjOcCAiwzsaSLZfKsl2dU/pLjsai7a/PMs6ZUadO6jKwmRAarU6AyF31qyah03ygweP5tGvDufxr63iBsin27Yjv5bps4N++y8gg2fjZ+IUNAsKTs605yP15gPGySgTed/8iUNHjeT3l/4GR3KJlwDQKf/OsuT5Lebf+GGz7U/bKV1P2xj/50XXf/jr5zmIwkbMGYaBxPAD/QGr7lhsP0fSnKiM4S3Y7P6JmSuQSISQDAPa0WaihkZKbCj86vU4rmBpHcfQp1efpNnbqzgQgaZ16QmP2Bj7kDxFzfg7DqYVq/7wXzYIEFkMHneMuoxdAJNmrssW58NqnbLb3uYOcR9xnp6cOtay+cGcctbXhSfjX9uENVPepGDBYxCI2R0XqtB2n2Teb1kocrNHsXOCqKipwRWgwUiAfhtXgZXoSE9ml7dKFK5CVliHNS0XX9K6jOCy1pIBMrVSaI3Js3LM9hV8gA2ulr5Gio1ohCLlUcPRtSBI3+aDxskiBpQKEZCg0kLVRizAGxEGGiix/2FlLBxEoP7DBSgc1Nkm/gJFxeoALGRBFoZVD1F0vThobHpDZaC7OwmKq6TRt9IYLcxF7sUg9lryUMDPx8pW48iohOpQ79R9Nq4WRTXaRAP8VI2Lw2fODdXsDmDRBdrrI9DShBaWbpYM3WzPlYdyU1jKlS5CZW0euj5QW/Rj9t2mw+Zrfz0625q3WcE8zeD3p5Bv2fD2cCN7N53iF4eO53vLyTCaixqrZXAC1txv2bF5wKKfzNZVbUZP6RQrD7Osi2SH4Z0Jlxx9brWERXjcIuK6yd0RCEiEWSEfYlM4NRv3ZccXV4jR5fBnPc3TOpD3m6v08TZS7mshAIo+OMbARvVDZD6IaKVHqhgLJd+JF0xsYCmxO9GmctBmrMrJ1Jojs+tyh6QT7/ZxMQZhjNWlGFJX3Zy4eIlmrn4M3aZd5epQ49Xb8ETHFYXw33lqDEOejIqgcHGXII5Dq7X4EMyOqLSBNW5TYhJ9F0DW3ZpoqrPk6y+M5I9iRMNhHTV4zpxpoisccz0BTwcQUi9+f4iXgQ6ZNxsUhxd2GcjTMyLGwFFueyL9dSqzxtUL+lFJvzjn3slQ1uyDiJnl8HUtt8oemnMdI6Iftu7P8fir1mOnThNb0yZz5ESyCVP96G0NQduBPLD1l3Utu9IeqJWPNMDD1RsxPQxcowAIRUY4QCVqYRKDdkNAmwYJuY5PFh4A4DNvX427zlRcy0SZUdsBtjYMlPQ3H0tNt8eS2wrTp9x4KrNnqV2/UbRwDffZ8sCCdVv1DQa9Nb7/Ddv96FU2u7l7A7NNIhpc+NGUGrC5PX1xi1MyGOyQ5kqoKvX4t8/MPEFHgSxa3aUZk4CZnDxqrXUtP0Ag2KNsJHN04PPlVNLBAoPoHYx4cGNIEbGdw0iKmvRBLE+/DM6p1BdB5Xr6jKYmj07gEtzmGPCZXd6F6vvd9HqHhghO66tjUT/cBi27FT17/BEwhU3FwVAgSb1Gs5RB4YkCgRIZPC7v9dwtsQSVp1DPwzDvIAN2wTgcAeoA2KNzcVk/B5Q/PtSntg9swBM5APPDXqLLaxQ5aZ8beXq+HkpdnaTJAS+GyU2NGUinLW5u1O5Oq04EjL4DRen4Jig0bTTqE0/at9/NI2aOp+pC6T4WPGAUBkPpHiUgyQb92d/L6jOpkFbHRWRHWUExTFHVD0Xw1UPhcsuzhK7DxnP5SH41btL1aEQQWVfCoKn08A3mflDtPBU3SS+odzcSEEJaoSbftnJbgcPHkQQXAEKAMVqtuDQDhnl9bpg8ZDhUmalu8i+I6dSz2GTmG1EtxWIrfEzl9D85V/Sus1bsyRKe/YdZtf4OK+kcFC44sES6/lBKw8gaPwLj0noGSa7t4YpelrJ2Fbk6zGUxs1czOFTRtWiZCx3FHUYMIZ3UQDo8GPgAxBnozvpVgrAwySHybPPG5N55OFauQ6IfIFZw2Y8cfUaNol2ZUO1ZhZU7lGPRK0Svh/kEvT4yTN0+q/zXPzACDTTvJiAUewoFumkYlGItd07BNnRLzTWG7ymRtO0/4aq8VGhsnNWaIz7qmj1M9U49+M1zPSBT8awhH/GDQ2fNJemL1xJ8c+/Sg9XbswltDHTFmSbqRWUoM0APX7vL1pFrXqPoHJ1Wxn8eNXmvAEM6oFQAI8oB25x6MQ5HO7dbAGFC0ayaC0nLDs1THbOx6ZlIdrA4NVikBK1Ewoh5i4e5TxSNNJFdm9vzq7embmYY1zwvfVa9eHf31/4KaftkfEvMDeCTVlQWED5qqAkNS2NLevw8RO8PcbSz9dz5dvu6cVxMUYeqjwc52ZQtOgScPIkh+pTzbhObCgoGuRUab9RQTj76debqDEm5RoJVCwy8Thi62ytOrOUkB2xoVGO5UVqOc6VrN2Gmj07kC9uztI1zLaBXp29dA3XJbGcAvEmOlERD2Ph0GffbrquX7xR4Xa15MsclSA6+eSrDcw+Yr5AlIEdex5PZwSRaADYzHuiBOJepNFcNa8WR5UbtaeOL4/lCARrJ/O7ZQdcDtrglq5eS51fG09PN+lIj9WITy4elbDKorjqXXeFLwRbYYbHuJ4Pi3H9VlzxUslYP0+QKPPDnSAE7DZ4PDVu259dS6CnGnEoeu5wE4jBP1q1llnCj9esv2FFIw16QDDDv7foU+5mRbgJPgZxOSr9iBTQ5nt/xUZssUhEDGsOTvvZwtP3sALgD1duShGam6MHcPLvLVzJoeHmrTvZxRw+fpL7D1HYhYKnBrG1Z/8R+mn7bvpqw8+06LNvucMVZbC4ZwdQxYbtSbD6qbjs3C3Iju7YztqMbbZSMsZZoYSmzxI178Vi0U4qUiOeQmMcVKaOn2NLWEkgBsXvuHFkT6BBS9g8FJXQmYvFaAtu0v6lG9bGbftRvaQ+ZHV3o5otn+PCBADDQ0VCgegHFHDAknPiVswaoCFgGMj6MJEiGYls+RzPPV0Hj+dqPrpiUXCYsfBTVvyOqjoSul7DJ1FS7+FUv/WLXG3C9wtXjaPHayRQqIy9wT3zyth9ed8zqlq19g9YZEd7UfWuD1M8KcWiXTxUmRsAGVXdIF+QYeHijc5NrIFJyOieQtCPm8rMJeRVkRjgPEzwVAfJE8dFYe69xkoFdGNlchkBEHPTgB9nzj4y3jjuM83SY+NEzjgRwoKRrN68E8fUUGTSyDGeqt+a420uAqPTKp18KhrpoOIxOrb83xSh6p3KJ9zAfiOQsFotSouqZ6Bk8x0tUbsNbyxu8AKB5Q1ZbzLQIwELBxgBy8mPovMKIABYAA5gMLJgwYHz5hXgnNTYxMvN9xQYMajmg8qFon3hgQoNWNHxBQ38HSML9wfjC1dcBHwisNchXmZRrUVwXJ0XCVUc0aLqXizavMm8SwMvRg2+cLPiYVyrkudDM22kGFDzOW6m8vXGpLcvRCM2D2hihmYmoJgHwTXxthfMWV+WVPcyvJ3EjGGepaiW8BAqDHghBL+fAHx3Hiwqs/X9fQ0+/s3W4HMGd/Sa/x8TbgTv0Yr3J3g2iLLb+1hN/REzhjckZTRXEd4fW/XsDuxlZ77Y/4/KJS9jFe9eQdb73bQNzSMi4ytZVPdQi82/n9e2W/9NWzffqLqxj1/6nqxJB0XNM1KKcj5jxizfUr58+Xsj1MQaktUzGXuQ4kTYkzQv69v/VYrAIH0vVkts0lFR1afjvQjYFNiM2d8S7KaLXXWxuy522WXAM1aX/dtBTy91BXYZtvlPSVbPDCHaUbfAtnXGgbFvNPaPxrbODPgNrjD7p+q1/bOTTkhWfb6kuhoG8dQ3W7AjOnZGxw7p2CmdL8D+b90ZHurm+zPuM+lYBDZqVxMblqhWu5AZm4KRhIR7sfc/3gEg2bwHLfakNA4L/1XvPLhWIeeow+Y7LKre6ZZoR92bv0F5LoIhJMXokZLV84Zk9e76973Nw0hYjPAO2zbro0XZHYOdl81Y3Cq523hhpqsf3uciWf3nr711KZBt/lNcC64TO08aIPP7dmy+ixarb2244hogRiZWDUlI+I8ZgFsukpbwZJjs9IiaZ5HF5j+MzXINt/JPeQMTMkTjFYfp7xtLkWz+o6KmL7Uouj88Mj7MfM+3VbB/HYaZpHkHSVbv95LmSQ1+G9OdqQxyxrvFALh3k2T1vgauo3g1VxHzvd4xgp2+BMXVQVT1uZLd/4tk810IpPnG+8Yyu5db7WKunTPrW/OQpPmxIftWSeOwrlNo5l6PO1juwp6ukup8xoI3m2r6clH1HLHYk5ItNn8atj7GPlTG+yDT13YHgVIAmn6ujPdBGjtLpkk2/yVR8x4VVO8KSfX2EDRn9VI164NQun5J606TUMUhhMqJtUVN7yXafbMlq3ebqHquwpICEyn3xBWoX08HGHt/pL+gzdhOT08Vrb7toi1prmD19BFUT50no9yS+R7+cSI2cheWNIcV7KGouueCkrTY/Hss9qTTFmMpBO+unt48HvQO31ytP91i+fNB7/DFA/WTBZO1zX/GYkvaK6mejehtFFRPH1Hx2Itrje9cv5wfKVW//v/QCCTK8eUtiruZaPMPEK3e+ZKq/yyq7hPcx5zD26nzBHaOb6fWUwRVPyUp7l8ETV8gWn0DJVWPw6sVQ2t4H8d1ma/1XyXY+zVMTSoNYktUXLqouHuKmj4Mu4RJdt98yeZbJVl9GyXNs1NU3UcE1XVWkF0pQSAb715PwTpDUXUflVR9l6R5N/EaFiytsPomC5p3OI8oWfegmxSvIi8w8uifIsU1V5FwVa8hqM5EvOxSiHFNEhXXJ+gbF1XXIUFxYdfeYLAVV7Kgug6LiutnUXGtEGJck7FYKFx2OcNkT61idTxPmM91u+T/AK9iJvxgAxKXAAAAAElFTkSuQmCC"
SOC_COL = "societe_id"
USERS_FILE = "users.csv"
DATA_FILES = {
    "base": "01_Donnees_base_source.csv",
    "indicators": "02_Indicateurs_source.csv",
    "history": "03_Indicateurs_historique.csv",
}
KEY_COLUMNS = [SOC_COL, "SIREN"]
STORAGE_ROOT = ".app_storage"
ACTIVE_DATASET_DIR = "active_dataset"
MANIFEST_FILE = "manifest.json"

VIGILANCE_ORDER = [
    "Vigilance Critique",
    "Vigilance Élevée",
    "Vigilance Modérée",
    "Vigilance Allégée",
    "Vigilance Aucune",
]

RISK_ORDER = [
    "Risque avéré",
    "Risque potentiel",
    "Risque mitigé",
    "Risque levé",
    "Non calculable",
    "Aucun risque détecté",
]

VIGILANCE_COUNT_COLUMNS = [f"Nb {label}" for label in VIGILANCE_ORDER]
RISK_COUNT_COLUMNS = [f"Nb {label}" for label in RISK_ORDER]
STATUS_COUNT_COLUMNS = VIGILANCE_COUNT_COLUMNS + RISK_COUNT_COLUMNS

BASE_RISK_SOURCE_COLUMN = "Statut de risque (import SaaS source)"
PORTFOLIO_PIPELINE_VERSION = "v195_analysis_indicator_tops"
CRITICAL_VIGILANCE = {"Vigilance Élevée", "Vigilance Critique"}
PRIORITY_RISK = {"Risque potentiel", "Risque avéré"}

REVIEW_FREQUENCY_DEFAULTS = {
    "Vigilance Critique": 3,
    "Vigilance Élevée": 6,
    "Vigilance Modérée": 12,
    "Vigilance Allégée": 24,
    "Vigilance Aucune": 36,
}

REVIEW_CAPACITY_DEFAULTS = {
    "Vigilance Critique": 5,
    "Vigilance Élevée": 8,
    "Vigilance Modérée": 10,
    "Vigilance Allégée": 12,
    "Vigilance Aucune": 15,
}

REVIEW_SIMULATIONS_FILE = "review_simulations_store.csv"
REVIEW_TYPE_BY_VIGILANCE = {
    "Vigilance Critique": "Revue critique immédiate",
    "Vigilance Élevée": "Revue renforcée",
    "Vigilance Modérée": "Revue ciblée",
    "Vigilance Allégée": "Revue allégée de mise à jour",
    "Vigilance Aucune": "Revue standard",
}

REVIEW_SIM_REAL_LABEL = "Statut de vigilance réel"
REVIEW_SIM_EST_LABEL = "Statut de vigilance estimé après remédiation"
REVIEW_SIM_TREND_LABEL = "Indicateur de tendance"
REVIEW_SIM_AI_STRUCTURED_LABEL = "Analyse IA structurée"
REVIEW_SIM_REAL_DISPLAY_LABEL = "Statut réel"
REVIEW_SIM_EST_DISPLAY_LABEL = "Statut estimé"
REVIEW_SIM_TREND_DISPLAY_LABEL = "Tendance"
REVIEW_SIM_NEXT_REVIEW_DISPLAY_LABEL = "Prochaine revue"
GEMINI_MODEL_DEFAULT = "gemini-2.5-flash"
GEMINI_MAX_BATCH_SIZE = 10
GEMINI_API_TIMEOUT_SECONDS = 60
REVIEW_SIM_GEMINI_KEY_STATE = "review_sim_gemini_api_key"
REVIEW_SIM_PDF_DIR = "review_simulation_pdfs"
REVIEW_SIM_PDF_FONT_REGULAR = "CMDejaVuSans"
REVIEW_SIM_PDF_FONT_BOLD = "CMDejaVuSans-Bold"
REVIEW_SIM_PDF_FONT_ITALIC = "CMDejaVuSans-Oblique"
REVIEW_SIM_PDF_FONT_BOLDITALIC = "CMDejaVuSans-BoldOblique"
CLASSIFICATION_PDF_PREFIX = "classification"
CLASSIFICATION_AXIS_ORDER = ["Client", "Pays", "Produit", "Canal"]
CLASSIFICATION_AXIS_LABELS = {
    "Segment / Client": "Client",
    "Indicateurs Pays": "Pays",
    "Indicateurs Produits": "Produit",
    "Indicateurs Canal": "Canal",
}
CLASSIFICATION_STATUS_COTATION = {
    "Risque avéré": "4",
    "Risque potentiel": "3",
    "Risque mitigé": "2",
    "Risque levé": "1",
    "Aucun risque détecté": "0",
    "Non calculable": "",
}
CLASSIFICATION_STATUS_NEW_COTATION = {
    "Risque avéré": "4",
    "Risque potentiel": "4 ou 3",
    "Risque mitigé": "2",
    "Risque levé": "1",
    "Aucun risque détecté": "0",
    "Non calculable": "",
}
CLASSIFICATION_STATUS_REAL_RISK = {
    "Risque avéré": "Risque avéré",
    "Risque potentiel": "Risque avéré ou Risque potentiel",
    "Risque mitigé": "Risque mitigé",
    "Risque levé": "Risque levé",
    "Aucun risque détecté": "Aucun risque détecté",
    "Non calculable": "",
}
CLASSIFICATION_EXCLUDED_INDICATORS = {"Vigilance"}
CLASSIFICATION_COMMENT_PLACEHOLDER_TEXT = "Commentaire absent (à compléter dans Beclm)."
CLASSIFICATION_AI_PLACEHOLDER_TEXT = "Analyse IA absente (à régénérer dans Revues & Simulations)."

INDICATOR_REFERENCE_COLUMNS = ["Famille", "Indicateur d’alerte", "Sens métier de l’indicateur pour l’IA"]
INDICATOR_REFERENCE_FILENAME_CANDIDATES = (
    "Référentiel Indicateurs actifs.xlsx",
    "Referentiel Indicateurs actifs.xlsx",
    "referentiel_indicateurs_actifs.xlsx",
)
REVIEW_SIM_INDICATOR_REFERENCE_STATE = "review_sim_indicator_reference_df"
REVIEW_SIM_INDICATOR_REFERENCE_SOURCE_STATE = "review_sim_indicator_reference_source"
REVIEW_SIM_INDICATOR_REFERENCE_EDITOR_KEY = "review_sim_indicator_reference_editor"
DEFAULT_INDICATOR_REFERENCE_ROWS = [
    (
        "Segment / Client",
        "Gel des avoirs société",
        "Vérifie si la personne morale elle-même correspond à une personne ou entité faisant l’objet d’un gel des avoirs ou d’une mesure de sanctions. Ne pas confondre avec un simple risque pays, une mauvaise presse ou un doute commercial. Toute correspondance positive ou non levée reste critique tant que l’identité n’est pas formellement confirmée ou écartée.",
    ),
    (
        "Segment / Client",
        "Gel des avoirs / personnes liées",
        "Vérifie si un dirigeant, bénéficiaire effectif, actionnaire significatif ou autre personne liée correspond à une personne visée par un gel des avoirs ou une mesure de sanctions. L’analyse doit distinguer une correspondance confirmée, une homonymie et un résultat non concluant.",
    ),
    (
        "Segment / Client",
        "PPE / personnes liées",
        "Mesure l’exposition de la société à une personne politiquement exposée ou à un proche ou associé de PPE parmi les personnes liées. Ne pas assimiler une simple notoriété publique à une PPE. L’enjeu est la vigilance renforcée liée à la fonction, au pays, au lien avec la société et à la date d’exercice.",
    ),
    (
        "Segment / Client",
        "Média négatifs / société",
        "Recherche des informations publiques défavorables crédibles sur la société pouvant signaler fraude, corruption, blanchiment, sanctions, criminalité financière ou atteinte grave à la réputation. Ne pas traiter comme un risque fort un article neutre, un litige commercial ordinaire ou une mention sans lien LCB-FT.",
    ),
    (
        "Segment / Client",
        "Média négatifs / personnes liées",
        "Recherche des informations publiques défavorables crédibles sur les dirigeants, bénéficiaires effectifs ou autres personnes liées. L’analyse doit distinguer la gravité des faits, leur actualité, leur fiabilité et leur lien réel avec la société et avec le risque LCB-FT.",
    ),
    (
        "Indicateurs Pays",
        "Risque pays GAFI",
        "Mesure l’exposition à un pays visé par les listes GAFI, liste noire ou liste grise selon le paramétrage BeCLM. Ne pas l’interpréter comme un simple pays étranger, un pays de résidence quelconque ou un flux international ordinaire.",
    ),
    (
        "Indicateurs Pays",
        "Risque pays UE",
        "Mesure l’exposition à un pays tiers à haut risque au sens du référentiel ou de la liste UE utilisée par BeCLM. Ne pas l’interpréter comme des relations avec l’Union européenne au sens large.",
    ),
    (
        "Indicateurs Pays",
        "Risque pays FR",
        "Mesure un signal de risque pays issu du référentiel France ou du paramétrage BeCLM. Ne jamais écrire que la France est un pays à risque sans élément explicite dans la donnée source. Il s’agit d’un classement interne ou référentiel, pas d’un jugement générique sur la France.",
    ),
    (
        "Indicateurs Pays",
        "Risque pays Bale Institute",
        "Mesure l’exposition à un pays présentant un niveau de risque selon un indice de type Basel AML Index ou référentiel équivalent. Ne pas le confondre avec une liste GAFI, une liste UE ou une liste de sanctions.",
    ),
    (
        "Segment / Client",
        "SIREN / Secteur d’activité",
        "Évalue si le secteur d’activité réel de la société est exposé par nature à des risques plus élevés : cash, flux internationaux, intermédiation, biens facilement transférables, actifs difficiles à valoriser, complexité opérationnelle ou secteurs fortement exposés à la fraude ou à l’opacité. Ne pas se limiter au code NAF si l’activité réelle diffère.",
    ),
    (
        "Segment / Client",
        "SIREN / Catégorie juridique",
        "Évalue si la forme juridique crée un risque particulier de complexité, interposition, opacité de gouvernance ou difficulté d’identification des parties prenantes. Ne pas considérer qu’une forme est risquée par principe ; le risque vient surtout de ce qu’elle permet en termes de structure, de contrôle et de transparence.",
    ),
    (
        "Segment / Client",
        "SIREN / N° d’immatriculation non trouvé",
        "Signale une anomalie d’identification légale : la société n’est pas retrouvée comme attendu dans les registres ou les données de référence. Ce n’est pas un risque pays ni un risque activité ; c’est d’abord un risque d’existence légale, de qualité de donnée ou d’usurpation.",
    ),
    (
        "Segment / Client",
        "SIREN / Société radiée",
        "Signale qu’une société est radiée, inactive ou juridiquement sortie du registre, ce qui remet en cause la poursuite normale de la relation d’affaires. Ne pas en déduire automatiquement une fraude, mais traiter cela comme une alerte critique d’existence légale tant que la situation n’est pas clarifiée.",
    ),
    (
        "Segment / Client",
        "BODACC / Dépôt des comptes",
        "Mesure le niveau de transparence comptable et de régularité déclarative de la société. Le risque augmente si l’absence de dépôt est répétée, ancienne ou incohérente avec la taille et l’activité. Ne pas confondre un retard isolé avec une opacité structurelle.",
    ),
    (
        "Segment / Client",
        "BODACC / Difficultés procédures collectives",
        "Mesure l’exposition à une procédure collective ou à une difficulté financière lourde. Ce n’est pas un indicateur direct de blanchiment, mais un signal de fragilité financière pouvant accroître le risque d’opérations atypiques, de pression de trésorerie ou de comportements opportunistes.",
    ),
    (
        "Segment / Client",
        "BODAC / Création récente",
        "Signale une société récemment créée, donc avec peu d’historique, peu de recul et une substance économique encore à démontrer. Le risque est surtout élevé si le niveau d’activité, la complexité ou les flux observés sont disproportionnés par rapport à l’ancienneté de la société.",
    ),
    (
        "Segment / Client",
        "BODACC / Modifications administration",
        "Mesure l’instabilité de gouvernance à travers les changements de dirigeants, administrateurs ou organes de gestion. Le risque augmente si les changements sont fréquents, récents, peu expliqués ou combinés à d’autres alertes. Un changement isolé et documenté n’a pas la même portée.",
    ),
    (
        "Segment / Client",
        "BODACC / Ventes et cession",
        "Signale des cessions, ventes ou transferts pouvant affecter la propriété, le contrôle ou les actifs de la société. Le risque porte sur la compréhension du changement de contrôle ou de substance, pas sur l’existence d’une cession en soi.",
    ),
    (
        "Segment / Client",
        "Risques Financiers / Part de l’EBIT dans le CA",
        "Mesure si la rentabilité opérationnelle rapportée au chiffre d’affaires paraît atypique au regard du secteur, de la taille ou de l’historique. Ne pas interpréter le ratio comme une preuve de fraude ; c’est un signal d’anomalie économique à expliquer.",
    ),
    (
        "Segment / Client",
        "Risques Financiers / Résultat courant avant impôts sur CA",
        "Mesure si le résultat courant avant impôts rapporté au chiffre d’affaires paraît anormalement élevé, faible ou instable. C’est un indicateur de cohérence économique et financière, pas un indicateur autonome de criminalité.",
    ),
    (
        "Segment / Client",
        "Risques Financiers / taux d’endettement",
        "Mesure le niveau de tension financière et de dépendance à l’endettement. Le risque est plus fort si l’endettement paraît incompatible avec l’activité, la rentabilité ou les flux observés, surtout combiné à d’autres signaux de fragilité.",
    ),
    (
        "Segment / Client",
        "Segment",
        "Situe la société dans un segment interne BeCLM ou une catégorie de clientèle ou d’activité censée porter un niveau de risque particulier. L’analyse doit s’appuyer sur le sens métier interne du segment et ne pas inventer seule ce que le segment signifie. Si le contenu exact du segment n’est pas explicité, rester prudent et l’indiquer.",
    ),
    (
        "Indicateurs Produits",
        "Produit(service) principal",
        "Évalue si le produit ou service principal présente un risque intrinsèque plus élevé en raison de sa complexité, de sa liquidité, de sa difficulté de valorisation, de son caractère intermédié, de son exposition au cash, de sa portabilité ou de sa dimension internationale. Expliquer le risque par les caractéristiques du produit, pas seulement par son nom.",
    ),
    (
        "Indicateurs Produits",
        "Part des opérations avec produits(services) hauts risques 12 m",
        "Mesure la part des opérations sur 12 mois portant sur des produits ou services classés haut risque par le référentiel interne BeCLM. L’analyse ne doit pas inventer seule ce qui est haut risque si la liste interne n’est pas fournie ; elle doit s’appuyer sur le classement BeCLM ou rester prudente.",
    ),
    (
        "Indicateurs Canal",
        "Canal principal 12m",
        "Identifie le canal dominant de la relation ou des opérations sur 12 mois : présentiel, distance, mail, tiers introducteur, onboarding intermédiaire, etc. Le risque porte sur la qualité du contact, la traçabilité, la présence éventuelle d’un tiers et le niveau de maîtrise du parcours. Éviter de mélanger plusieurs notions si elles ne sont pas explicitement présentes.",
    ),
    (
        "Indicateurs Canal",
        "Part des opérations à distance 12m",
        "Mesure la proportion d’opérations réalisées à distance sur 12 mois. Cet indicateur ne mesure ni le risque pays ni l’intermédiation par un tiers ; il mesure spécifiquement le caractère non présentiel et les besoins associés en contrôle d’identité, sécurité et traçabilité.",
    ),
    (
        "Indicateurs Produits",
        "Cash intensité",
        "Mesure la part de cash ou d’opérations assimilables au cash dans l’activité. Le risque vient de l’opacité, de la traçabilité plus faible et de la liquidité. Ne pas confondre espèces réelles, quasi-cash et simples flux bancaires classiques si la donnée ne le permet pas.",
    ),
    (
        "Indicateurs Pays",
        "Cross border",
        "Mesure l’intensité des flux, opérations ou relations transfrontalières, c’est-à-dire impliquant plusieurs pays. Ne pas en déduire automatiquement qu’un pays est sensible. Cet indicateur mesure d’abord le caractère international des flux, pas la dangerosité intrinsèque d’un pays. Si les pays concernés ne sont pas connus, écrire pays à préciser et ne pas en inventer.",
    ),
]
INDICATOR_REFERENCE_DEFAULT_SOURCE_LABEL = "Référentiel durci intégré BeCLM."
INDICATOR_REFERENCE_GLOBAL_GUARDRAILS = [
    "Ne jamais inventer un pays, une personne, un fait ou un flux absent de la fiche client.",
    "Ne jamais traiter GAFI, UE, FR, Bale Institute et Cross border comme des synonymes.",
    "Toujours raisonner à partir du sens métier de l’indicateur avant de proposer une action.",
    "Quand une donnée métier précise manque, écrire à préciser plutôt que produire une interprétation libre.",
    "Ne pas transformer un classement interne BeCLM en affirmation générale sur un pays, un secteur ou une forme juridique.",
    "Les valeurs détaillées, seuils, règles de calcul et paramétrages internes BeCLM ne sont pas communiqués à l’IA ; ils ne doivent jamais être supposés.",
    "Le dispositif proposé doit venir de la nature de l’alerte et des meilleures pratiques de due diligence, pas d’une logique interne BeCLM supposée.",
]
BECLM_METHODOLOGY_FRAME = {
    "limites_information": [
        "Les valeurs détaillées des indicateurs, les seuils de déclenchement, les pondérations et les paramétrages internes BeCLM ne sont pas communiqués à l’IA.",
        "Le statut d’un indicateur ne permet pas, à lui seul, de déduire le motif exact de déclenchement ni la règle interne utilisée par BeCLM.",
        "L’IA ne doit jamais construire une recommandation comme si elle connaissait une valeur cachée, un seuil interne ou une configuration BeCLM non fournie dans la fiche.",
    ],
    "posture_attendue": [
        "L’IA agit comme un compliance officer senior spécialisé KYC / EDD / LCB-FT.",
        "Pour chaque alerte, l’IA applique les meilleures pratiques de due diligence adaptées à la nature de l’alerte, de façon proportionnée, traçable, opérationnelle et défendable.",
        "Quand une donnée manque, l’IA le dit explicitement et propose la diligence standard la plus pertinente sans extrapoler sur une logique interne cachée.",
    ],
    "exemples_imperatifs": [
        "Exemple Risque pays UE : si le pays exact, la contrepartie ou le flux précis ne sont pas explicitement fournis, ne nommer aucun pays ; raisonner sur une alerte géographique potentiellement sensible au sens UE et écrire pays concerné à préciser si nécessaire.",
        "Exemple SIREN / Catégorie juridique : si la forme juridique exacte ou la logique de classement BeCLM ne sont pas fournies, ne pas inventer la raison précise du déclenchement ; proposer les diligences usuelles liées à une structure juridique potentiellement complexe, opaque ou à clarifier.",
    ],
}
INDICATOR_REFERENCE_INTERPRETATION_LIMITS = {
    "Risque pays GAFI": "La valeur détaillée, le pays exact et la règle de déclenchement interne ne sont pas communiqués ; ne pas nommer un pays absent de la fiche et raisonner sur une vigilance géographique au sens GAFI.",
    "Risque pays UE": "La valeur détaillée, le pays exact et la règle de déclenchement interne ne sont pas communiqués ; ne pas nommer un pays absent de la fiche et raisonner sur une vigilance géographique au sens UE.",
    "Risque pays FR": "La valeur détaillée et la logique interne de classement France / BeCLM ne sont pas communiquées ; ne pas transformer cet indicateur en affirmation générale sur la France ou sur un pays précis.",
    "Risque pays Bale Institute": "La valeur détaillée, le pays exact et la logique de score type Basel / Bale ne sont pas communiqués ; raisonner sur un signal de risque géographique fondé sur un indice et non sur une liste de sanctions ou GAFI.",
    "Cross border": "La valeur détaillée et les flux précis ne sont pas nécessairement communiqués ; ne pas nommer un pays ou une contrepartie absents de la fiche et raisonner sur le caractère transfrontalier des opérations.",
    "SIREN / Catégorie juridique": "La forme juridique exacte ayant motivé le signal et la logique interne BeCLM ne sont pas forcément communiquées ; ne pas inventer la raison précise du déclenchement.",
    "Segment": "Le sens détaillé du segment peut relever d’une classification interne BeCLM ; ne pas inventer la logique exacte du segment si elle n’est pas fournie.",
    "Produit(service) principal": "Le détail de la taxonomie interne des produits sensibles n’est pas entièrement communiqué ; ne pas inventer une logique interne cachée et raisonner sur la nature du produit explicitement visible.",
    "Part des opérations avec produits(services) hauts risques 12 m": "La liste exacte des produits classés haut risque et les seuils internes BeCLM ne sont pas communiqués ; ne pas inventer le motif précis de classement.",
    "Canal principal 12m": "Le détail complet du paramétrage canal BeCLM n’est pas communiqué ; ne pas déduire une logique interne cachée à partir du seul libellé.",
    "Part des opérations à distance 12m": "Le seuil interne exact et les règles de scoring distance ne sont pas communiqués ; raisonner sur les meilleures pratiques liées au non-présentiel sans surinterpréter une valeur cachée.",
}
INDICATOR_REFERENCE_DUE_DILIGENCE_GUIDANCE = {
    "Risque pays GAFI": "Appliquer les meilleures pratiques de due diligence géographique : identifier les pays et contreparties concernés s’ils sont connus, comprendre la nature des flux, vérifier la cohérence économique et documenter les contreparties et justificatifs associés.",
    "Risque pays UE": "Appliquer les meilleures pratiques de due diligence géographique : identifier les pays et contreparties concernés s’ils sont connus, comprendre la nature des flux, vérifier la cohérence économique et documenter les contreparties et justificatifs associés.",
    "Risque pays FR": "Appliquer les meilleures pratiques de clarification du signal géographique : comprendre l’exposition réelle, documenter le pays ou le rattachement concerné s’il est connu et conserver une formulation prudente si le motif exact n’est pas communiqué.",
    "Risque pays Bale Institute": "Appliquer les meilleures pratiques de due diligence géographique en vérifiant la réalité de l’exposition internationale, les contreparties, les flux, leur cohérence économique et la documentation disponible.",
    "Cross border": "Appliquer les meilleures pratiques sur les flux transfrontaliers : identifier les pays, contreparties, motifs économiques, circuits financiers, documents commerciaux et éléments de traçabilité lorsque ces informations sont disponibles.",
    "SIREN / Catégorie juridique": "Appliquer les meilleures pratiques de due diligence structurelle : clarifier la forme juridique, la gouvernance, les organes de contrôle, les pouvoirs, les bénéficiaires effectifs, l’objet social et la substance de la structure.",
    "Segment": "Appliquer les meilleures pratiques liées à une classification interne : confirmer le segment retenu, vérifier sa cohérence avec l’activité, la taille, les flux et le profil du client, et documenter les diligences proportionnées au segment.",
    "Produit(service) principal": "Appliquer les meilleures pratiques de due diligence produit : comprendre la nature du produit ou service, ses caractéristiques sensibles, sa clientèle, ses flux, son circuit économique et les justificatifs métier pertinents.",
    "Part des opérations avec produits(services) hauts risques 12 m": "Appliquer les meilleures pratiques de due diligence produit : identifier les produits ou services concernés, leur poids réel dans l’activité, la justification économique et les contrôles associés.",
    "Canal principal 12m": "Appliquer les meilleures pratiques de due diligence canal : documenter le parcours client, la présence de tiers, les modalités d’entrée en relation, les points de contrôle et la traçabilité.",
    "Part des opérations à distance 12m": "Appliquer les meilleures pratiques de due diligence non présentielle : fiabilisation de l’identité, preuves de parcours, contrôles de cohérence, sécurité et conservation des traces.",
}
INDICATOR_REFERENCE_STRICT_RULES = {
    "Risque pays GAFI": {
        "must_include_any": ["gafi", "liste grise", "liste noire"],
        "must_not_include": ["union europeenne au sens large"],
    },
    "Risque pays UE": {
        "must_include_any": ["ue", "union européenne", "liste ue", "pays tiers"],
        "must_not_include": ["gafi"],
    },
    "Risque pays FR": {
        "must_include_any": ["référentiel", "france", "paramétrage", "classement interne"],
        "must_not_include": ["la france est un pays à risque", "france est un pays à risque"],
    },
    "Risque pays Bale Institute": {
        "must_include_any": ["bale", "basel", "indice", "index"],
        "must_not_include": ["gafi", "liste de sanctions"],
    },
    "Cross border": {
        "must_include_any": ["transfrontal", "international", "plusieurs pays", "cross-border"],
        "must_not_include": ["liste gafi", "liste ue", "sanctions"],
    },
    "Segment": {"must_include_any": ["segment", "classification interne", "catégorie"], "must_not_include": []},
    "SIREN / Catégorie juridique": {"must_include_any": ["forme juridique", "structure", "gouvernance", "transparence"], "must_not_include": []},
    "SIREN / Secteur d’activité": {"must_include_any": ["secteur", "activité", "réel"], "must_not_include": []},
    "Produit(service) principal": {"must_include_any": ["produit", "service", "caractéristiques"], "must_not_include": []},
    "Part des opérations avec produits(services) hauts risques 12 m": {"must_include_any": ["haut risque", "12 mois", "part des opérations"], "must_not_include": []},
    "Canal principal 12m": {"must_include_any": ["canal", "parcours", "tiers", "présentiel", "distance"], "must_not_include": []},
    "Part des opérations à distance 12m": {"must_include_any": ["distance", "non présentiel", "12 mois"], "must_not_include": []},
    "Cash intensité": {"must_include_any": ["cash", "espèces", "traçabilité", "liquidité"], "must_not_include": []},
    "Risques Financiers / Part de l’EBIT dans le CA": {"must_include_any": ["ebit", "rentabilité", "ratio"], "must_not_include": []},
    "Risques Financiers / Résultat courant avant impôts sur CA": {"must_include_any": ["résultat courant", "ratio", "cohérence"], "must_not_include": []},
    "Risques Financiers / taux d’endettement": {"must_include_any": ["endettement", "tension financière", "ratio"], "must_not_include": []},
}
GEMINI_BASE_SOURCE_PREFIX = "Base source :: "
GEMINI_INDICATORS_SOURCE_PREFIX = "Indicateurs source :: "
PDF_DEPENDENCY_ERROR_MESSAGE = (
    "Génération PDF indisponible : la dépendance Python 'reportlab' n'est pas installée sur l'environnement de déploiement. "
    "Ajoutez 'reportlab' dans requirements.txt puis redéployez l'application."
)
VIGILANCE_RANK = {label: idx for idx, label in enumerate(VIGILANCE_ORDER)}
RISK_RANK = {label: idx for idx, label in enumerate(RISK_ORDER)}
REVIEW_OBJECTIVES_BY_VIGILANCE = {
    "Vigilance Critique": (
        "Sécuriser immédiatement le dossier et confirmer ou infirmer les alertes majeures.",
        "Documenter une décision de remédiation prioritaire et fixer une revue rapprochée.",
    ),
    "Vigilance Élevée": (
        "Compléter rapidement l’analyse et consolider les zones de risque sensibles.",
        "Valider la cohérence du dossier, des flux et des justificatifs avant réévaluation.",
    ),
    "Vigilance Modérée": (
        "Traiter les anomalies ciblées et remettre le dossier à jour sans surmobiliser les équipes.",
        "Programmer une prochaine revue cohérente avec le niveau de risque résiduel.",
    ),
    "Vigilance Allégée": (
        "Régulariser les points mineurs de complétude ou de pilotage identifiés sur le dossier.",
        "Confirmer que le suivi peut rester allégé avec une prochaine revue planifiée.",
    ),
    "Vigilance Aucune": (
        "Vérifier l’hygiène documentaire et la cohérence générale du dossier sans signe d’alerte majeur.",
        "Maintenir un cycle de revue standard et des données de pilotage à jour.",
    ),
}

FILTER_MAPPING = {
    "Segment": "Segment",
    "Pays": "Pays de résidence",
    "Produit": "Produit(service) principal",
    "Canal": "Canal d’opérations principal 12 mois",
    "Vigilance": "Vigilance",
    "Risque": "Risque",
    "EDD": "Statut EDD",
    "Analyste": "Analyste",
    "Valideur": "Valideur",
}

ANALYSIS_STATUS_ORDER = list(RISK_ORDER)
ANALYSIS_STATUS_DISPLAY = {
    "Aucun risque détecté": "Sans risque",
}
ANALYSIS_STATUS_SHORT_LABELS = {
    "Risque avéré": "Avéré",
    "Risque potentiel": "Potentiel",
    "Risque mitigé": "Mitigé",
    "Risque levé": "Levé",
    "Non calculable": "Non calc.",
    "Aucun risque détecté": "Sans risque",
}
ANALYSIS_FAMILY_ORDER = [
    "Segment / Client",
    "Indicateurs Pays",
    "Indicateurs Produits",
    "Indicateurs Canal",
]
ANALYSIS_FRESHNESS_ORDER = [
    "< 30 jours",
    "30 à 90 jours",
    "> 90 jours",
    "Sans date",
]
ANALYSIS_TOP_STATUS_SPECS = [
    ("Risque avéré", "Nb avéré", "% avéré"),
    ("Risque potentiel", "Nb potentiel", "% potentiel"),
    ("Risque mitigé", "Nb mitigé", "% mitigé"),
    ("Risque levé", "Nb levé", "% levé"),
    ("Non calculable", "Nb NC", "% NC"),
    ("Aucun risque détecté", "Nb sans risque", "% sans risque"),
]
ANALYSIS_TOP_SORT_OPTIONS = [
    "Nb",
    "%",
    "Nb avéré",
    "% avéré",
    "Nb potentiel",
    "% potentiel",
    "Nb mitigé",
    "% mitigé",
    "Nb levé",
    "% levé",
    "Nb NC",
    "% NC",
    "Nb sans risque",
    "% sans risque",
]
ANALYSIS_TOP_AXIS_CONFIG = [
    ("Top segment / client", "Segment / Client", "segment_client"),
    ("Top pays", "Indicateurs Pays", "pays"),
    ("Top produits", "Indicateurs Produits", "produits"),
    ("Top canaux", "Indicateurs Canal", "canaux"),
]
ANALYSIS_TOP_PERCENT_STYLE = {
    "%": {"base": "#5E8FC7", "text": "#163A59"},
    "% avéré": {"base": "#D92D20", "text": "#7A271A"},
    "% potentiel": {"base": "#F79009", "text": "#8A4B00"},
    "% mitigé": {"base": "#22C55E", "text": "#166534"},
    "% levé": {"base": "#16A34A", "text": "#14532D"},
    "% NC": {"base": "#94A3B8", "text": "#475569"},
    "% sans risque": {"base": "#16A34A", "text": "#14532D"},
}
ANALYSIS_SCREEN_CACHE_VERSION = "v209_analysis_committee_pdf"
ANALYSIS_PORTFOLIO_FILTER_LABELS = ["Vigilance", "Risque", "EDD", "Segment", "Pays", "Produit", "Canal", "Analyste", "Valideur"]
ANALYSIS_INDICATOR_FILTER_KEYS = ["Indicateur", "Statut", "Famille", "Fraîcheur"]
ANALYSIS_INDICATOR_FAMILY_EXACT = {
    "Segment / Client": {
        "ppe",
        "pep",
        "gel des avoirs",
        "media negatifs",
        "médias négatifs",
        "media negatif",
        "média négatif",
        "siren / categorie juridique",
        "siren / catégorie juridique",
        "bodacc / depot des comptes",
        "bodacc / dépôt des comptes",
    },
    "Indicateurs Pays": {
        "gafi",
        "fatf",
        "ue",
        "eu",
        "fr",
        "france",
        "bale",
        "bâle",
        "basel",
    },
}
ANALYSIS_INDICATOR_FAMILY_KEYWORDS = {
    "Indicateurs Pays": [
        "gafi", "fatf", "ue", "eu", "fr", "france", "bale", "bâle", "basel", "pays", "geo", "géograph",
        "geograph", "jurid", "territoire", "sanction", "cross border", "cross-border",
        "residence", "résidence", "nationalite", "nationalité", "offshore",
    ],
    "Indicateurs Produits": [
        "produit", "service", "cash", "especes", "espèces", "virement", "transfert", "carte",
        "compte", "wallet", "crypto", "instrument", "cheque", "chèque", "prelevement",
        "prélèvement", "depot", "dépôt", "mandat",
    ],
    "Indicateurs Canal": [
        "canal", "distance", "digital", "intermedia", "intermédia", "apporteur", "correspondance",
        "correspondant", "online", "web", "mobile", "agence", "face a face", "face-à-face",
        "onboarding", "on boarding", "souscription",
    ],
}

DISPLAY_COLUMNS = [
    "SIREN",
    "Dénomination",
    "Vigilance",
    "Risque",
    SOC_COL,
    "Pays de résidence",
    "Segment",
    "Produit(service) principal",
    "Canal d’opérations principal 12 mois",
    "Statut EDD",
    "Flag justificatif complet",
    "Analyste",
    "Valideur",
    "Date dernière revue",
    "Date prochaine revue",
    "Vigilance Date de mise à jour",
    "Nb historique",
    "Score priorité",
    "Motifs",
]

REQUIRED_COLUMNS = {
    "base": [SOC_COL, "SIREN", "Dénomination"],
    "indicators": [SOC_COL, "SIREN", "Vigilance statut", "Vigilance Date de mise à jour"],
    "history": [SOC_COL, "SIREN"],
    "users": ["username", "password", "role", "societes_autorisees", "enabled"],
}


class DataValidationError(ValueError):
    pass


class NoPublishedDatasetError(FileNotFoundError):
    pass


def render_html_block(html: str) -> None:
    html_renderer = getattr(st, "html", None)
    if callable(html_renderer):
        html_renderer(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


def inject_review_sim_toolbar_style() -> None:
    render_html_block(
        f"""
        <style>
        .st-key-review_toolbar_clear button,
        .st-key-review_toolbar_apply button,
        .st-key-review_toolbar_gemini button,
        .st-key-review_toolbar_pdf button,
        .st-key-review_toolbar_zip_pdf button,
        .st-key-review_toolbar_csv button {{
            border-radius: 14px;
            border: 1px solid rgba(22, 58, 89, 0.10) !important;
            font-weight: 800;
            padding: 0.6rem 1rem;
            box-shadow: 0 10px 24px rgba(22, 58, 89, 0.14);
            background: linear-gradient(135deg, {PRIMARY_COLOR}, #245782) !important;
            color: #FFFFFF !important;
        }}

        .st-key-review_toolbar_clear button:hover,
        .st-key-review_toolbar_apply button:hover,
        .st-key-review_toolbar_gemini button:hover,
        .st-key-review_toolbar_pdf button:hover,
        .st-key-review_toolbar_zip_pdf button:hover,
        .st-key-review_toolbar_csv button:hover {{
            color: #FFFFFF !important;
            filter: brightness(1.04);
            transform: translateY(-1px);
        }}

        .st-key-review_toolbar_clear button:disabled,
        .st-key-review_toolbar_apply button:disabled,
        .st-key-review_toolbar_gemini button:disabled,
        .st-key-review_toolbar_pdf button:disabled,
        .st-key-review_toolbar_zip_pdf button:disabled,
        .st-key-review_toolbar_csv button:disabled {{
            background: linear-gradient(135deg, rgba(22, 58, 89, 0.38), rgba(36, 87, 130, 0.38)) !important;
            color: rgba(255, 255, 255, 0.80) !important;
            box-shadow: none;
            transform: none;
            cursor: not-allowed;
        }}

        .st-key-review_sim_manual_status label[data-testid="stWidgetLabel"] p {{
            font-family: 'Sora', sans-serif;
            font-weight: 800;
            color: {PRIMARY_COLOR};
        }}

        .st-key-review_sim_manual_status div[data-baseweb="select"] > div {{
            min-height: 2.78rem;
            border-radius: 14px !important;
            border: 1px solid rgba(22, 58, 89, 0.18) !important;
            background: #FFFFFF !important;
            box-shadow: 0 8px 20px rgba(22, 58, 89, 0.08);
        }}

        .st-key-review_sim_manual_status div[data-baseweb="select"] * {{
            color: {PRIMARY_COLOR} !important;
        }}
        </style>
        """
    )



def inject_brand_theme() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Sora:wght@500;600;700;800&family=Montserrat:wght@600;700;800&family=Cormorant+Garamond:wght@500;600;700&display=swap');

        :root {{
            --cm-primary: {PRIMARY_COLOR};
            --cm-secondary: {SECONDARY_COLOR};
            --cm-accent: {ACCENT_COLOR};
            --cm-card: {CARD_BACKGROUND};
            --cm-text: #12263A;
            --cm-muted: #5B6B7F;
            --cm-white: #FFFFFF;
            --cm-border: rgba(22, 58, 89, 0.12);
        }}

        html, body, [class*="css"] {{
            font-family: 'Manrope', sans-serif;
            color: var(--cm-text);
        }}

        .stApp {{
            background:
                radial-gradient(circle at top right, rgba(94, 143, 199, 0.18), transparent 24%),
                linear-gradient(180deg, #f9fbff 0%, #eef5fd 45%, #f9fbff 100%);
        }}

        h1, h2, h3, .cm-heading, [data-testid="stMetricLabel"] {{
            font-family: 'Sora', sans-serif !important;
            letter-spacing: 0.01em;
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #163A59 0%, #1E4C73 100%);
            color: white;
            border-right: 1px solid rgba(255,255,255,0.08);
        }}

        [data-testid="stSidebar"] * {{
            color: white;
        }}

        [data-testid="stSidebar"] .stMarkdown p,
        [data-testid="stSidebar"] .stCaption {{
            color: rgba(255,255,255,0.88) !important;
        }}

        [data-testid="stSidebar"] .stMultiSelect label,
        [data-testid="stSidebar"] .stFileUploader label,
        [data-testid="stSidebar"] .stTextInput label {{
            color: white !important;
        }}

        .cm-sidebar-brand {{
            display: flex;
            align-items: center;
            gap: 0.9rem;
            padding: 0.25rem 0 1rem 0;
        }}

        .cm-sidebar-brand img {{
            width: 64px;
            height: 64px;
            border-radius: 0;
            box-shadow: none;
            background: transparent;
            object-fit: contain;
        }}

        .cm-sidebar-brand-title {{
            font-family: 'Sora', sans-serif;
            font-size: 1.02rem;
            font-weight: 800;
            line-height: 1.05;
            letter-spacing: 0.04em;
        }}

        .cm-sidebar-brand-subtitle {{
            font-size: 0.82rem;
            opacity: 0.88;
            margin-top: 0.15rem;
        }}

        .cm-hero {{
            background:
                linear-gradient(135deg, rgba(22, 58, 89, 0.98), rgba(36, 87, 130, 0.94)),
                radial-gradient(circle at top right, rgba(255,255,255,0.14), transparent 28%);
            border: 1px solid rgba(255,255,255,0.08);
            color: white;
            border-radius: 28px;
            padding: 2rem 2rem 1.8rem 2rem;
            margin: 0 0 1.25rem 0;
            box-shadow: 0 18px 40px rgba(22, 58, 89, 0.18);
        }}

        .cm-hero-grid {{
            display: grid;
            grid-template-columns: 1.6fr 0.7fr;
            gap: 1.25rem;
            align-items: center;
        }}

        .cm-hero-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            border: 1px solid rgba(255,255,255,0.16);
            background: rgba(255,255,255,0.09);
            border-radius: 999px;
            padding: 0.35rem 0.8rem;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }}

        .cm-hero h1 {{
            margin: 0.7rem 0 0.35rem 0;
            color: white;
            font-size: clamp(2.2rem, 3.4vw, 3.9rem);
            line-height: 0.96;
            letter-spacing: 0.02em;
        }}

        .cm-hero-subtitle {{
            margin: 0.25rem 0 0.45rem 0;
            font-family: 'Cormorant Garamond', serif !important;
            font-size: clamp(1.45rem, 2.15vw, 2.15rem) !important;
            font-weight: 600;
            line-height: 1.15 !important;
            letter-spacing: 0.01em;
            color: rgba(255,255,255,0.96) !important;
            max-width: 950px;
        }}

        .cm-hero-body {{
            margin: 0.45rem 0 0 0;
            font-family: 'Manrope', sans-serif !important;
            font-size: 1.03rem !important;
            font-weight: 500;
            line-height: 1.65 !important;
            color: rgba(255,255,255,0.88) !important;
            max-width: 900px;
        }}

        .cm-hero-note {{
            font-size: 0.96rem !important;
            color: rgba(255,255,255,0.82) !important;
        }}

        .cm-home-link {{
            margin-top: 0.55rem;
            text-align: center;
            font-family: 'Sora', sans-serif;
            font-size: 1rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            color: var(--cm-primary);
        }}

        .cm-hero-logo-card {{
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 210px;
            background: transparent;
            border: none;
            border-radius: 0;
            backdrop-filter: none;
        }}

        .cm-hero-logo-card img {{
            width: min(210px, 100%);
            height: auto;
            filter: drop-shadow(0 18px 26px rgba(0,0,0,0.14));
        }}

        .cm-section-title {{
            font-family: 'Montserrat', sans-serif;
            color: var(--cm-primary);
            letter-spacing: 0.02em;
        }}

        .cm-subsection-title {{
            font-family: 'Montserrat', sans-serif;
            color: var(--cm-primary);
            font-size: 1.04rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            margin: 0 0 0.55rem 0;
            min-height: 1.75rem;
            display: flex;
            align-items: flex-end;
        }}

        [data-testid="stMetric"] {{
            background: rgba(255,255,255,0.76);
            border: 1px solid var(--cm-border);
            border-radius: 20px;
            padding: 0.9rem 0.9rem 0.8rem 0.9rem;
            box-shadow: 0 10px 24px rgba(22, 58, 89, 0.06);
        }}

        [data-testid="stMetricValue"] {{
            font-family: 'Montserrat', sans-serif;
            color: var(--cm-primary);
        }}

        .cm-kpi-band {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.75rem;
            margin: 0.45rem 0 0.25rem 0;
        }}

        .cm-kpi-card {{
            background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(246,250,255,0.92));
            border: 1px solid rgba(22, 58, 89, 0.10);
            border-radius: 18px;
            padding: 0.7rem 0.85rem 0.72rem 0.85rem;
            box-shadow: 0 8px 20px rgba(22, 58, 89, 0.06);
            min-height: 84px;
        }}

        .cm-kpi-card.is-alert {{
            border-color: rgba(180, 42, 42, 0.16);
            background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(255,245,245,0.92));
        }}

        .cm-kpi-label {{
            font-family: 'Sora', sans-serif;
            font-size: 0.72rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #65758A;
            margin-bottom: 0.22rem;
        }}

        .cm-kpi-value {{
            font-family: 'Montserrat', sans-serif;
            font-size: 1.62rem;
            font-weight: 800;
            line-height: 1.05;
            color: var(--cm-primary);
            margin-bottom: 0.08rem;
        }}

        .cm-kpi-card.is-alert .cm-kpi-value {{
            color: #A22828;
        }}

        .cm-kpi-sub {{
            font-size: 0.78rem;
            color: var(--cm-muted);
            line-height: 1.25;
        }}

        .cm-kpi-note {{
            margin-top: 0.35rem;
            font-size: 0.82rem;
            color: var(--cm-muted);
        }}

        .stButton > button, .stDownloadButton > button, .stFileUploader button {{
            border-radius: 14px;
            border: none !important;
            font-weight: 800;
            padding: 0.6rem 1rem;
            box-shadow: 0 10px 24px rgba(22, 58, 89, 0.14);
            background: linear-gradient(135deg, var(--cm-primary), #245782) !important;
            color: #FFFFFF !important;
        }}

        .stButton > button[kind="secondary"], .stDownloadButton > button[kind="secondary"] {{
            background: linear-gradient(135deg, #245782, #2F6B9E) !important;
            color: #FFFFFF !important;
            border: none !important;
        }}

        .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{
            background: linear-gradient(135deg, var(--cm-primary), #245782) !important;
            color: #FFFFFF !important;
            border: none !important;
        }}

        .stButton > button:hover, .stDownloadButton > button:hover, .stFileUploader button:hover {{
            color: #FFFFFF !important;
            filter: brightness(1.04);
            transform: translateY(-1px);
        }}

        [data-testid="stSidebar"] .stButton > button,
        [data-testid="stSidebar"] .stDownloadButton > button,
        [data-testid="stSidebar"] .stFileUploader button {{
            background: linear-gradient(135deg, var(--cm-primary), #245782) !important;
            color: #FFFFFF !important;
            border: none !important;
        }}

        [data-testid="stSidebar"] .stButton > button[kind="secondary"],
        [data-testid="stSidebar"] .stDownloadButton > button[kind="secondary"] {{
            background: linear-gradient(135deg, #245782, #2F6B9E) !important;
            color: #FFFFFF !important;
            border: none !important;
        }}

        [data-testid="stSidebar"] .stFileUploader button:hover,
        [data-testid="stSidebar"] .stButton > button:hover,
        [data-testid="stSidebar"] .stDownloadButton > button:hover {{
            color: #FFFFFF !important;
            filter: brightness(1.05);
        }}

        div[data-testid="stFileUploaderDropzone"] {{
            background: rgba(22, 58, 89, 0.05) !important;
            border: 1px dashed rgba(22, 58, 89, 0.25) !important;
            border-radius: 16px !important;
        }}

        div[data-testid="stFileUploaderDropzone"] * {{
            color: var(--cm-primary) !important;
        }}

        [data-testid="stSidebar"] div[data-testid="stFileUploaderDropzone"] {{
            background: rgba(255,255,255,0.08) !important;
            border: 1px dashed rgba(255,255,255,0.30) !important;
        }}

        [data-testid="stSidebar"] div[data-testid="stFileUploaderDropzone"] * {{
            color: #FFFFFF !important;
        }}

        div[data-testid="stExpander"] {{
            border: none !important;
            background: transparent !important;
        }}

        div[data-testid="stExpander"] details {{
            border: none !important;
            background: transparent !important;
        }}

        div[data-testid="stExpander"] summary {{
            background: linear-gradient(135deg, var(--cm-primary), #245782) !important;
            color: #FFFFFF !important;
            border-radius: 14px !important;
            padding: 0.35rem 0.8rem !important;
            box-shadow: 0 10px 20px rgba(22, 58, 89, 0.12);
        }}

        div[data-testid="stExpander"] summary p,
        div[data-testid="stExpander"] summary span,
        div[data-testid="stExpander"] summary svg {{
            color: #FFFFFF !important;
            fill: #FFFFFF !important;
            font-weight: 800 !important;
        }}

        [data-testid="stDataFrame"], .stAlert, div[data-baseweb="select"], .stTextInput > div > div,
        .stMultiSelect > div > div {{
            border-radius: 16px !important;
        }}

        .stDataFrame {{
            border: 1px solid var(--cm-border);
            box-shadow: 0 10px 24px rgba(22, 58, 89, 0.05);
        }}

        [data-testid="stDataFrame"] [role="columnheader"] {{
            background: var(--cm-primary) !important;
            color: #FFFFFF !important;
            justify-content: center !important;
            text-align: center !important;
            font-family: 'Sora', sans-serif !important;
            font-size: 0.78rem !important;
            font-weight: 800 !important;
            letter-spacing: 0.05em !important;
            font-variant-caps: all-small-caps !important;
            text-transform: none !important;
            border-bottom: 0 !important;
        }}

        [data-testid="stDataFrame"] [role="columnheader"] * {{
            color: #FFFFFF !important;
            text-align: center !important;
        }}

        [data-testid="stDataFrame"] [role="gridcell"] {{
            justify-content: center !important;
            text-align: center !important;
        }}

        [data-testid="stDataFrame"] [role="gridcell"] * {{
            text-align: center !important;
        }}

        .cm-block-caption {{
            color: var(--cm-muted);
            margin-top: -0.2rem;
        }}

        .cm-table-panel-title {{
            display: block;
            width: 100%;
            background: var(--cm-primary);
            color: #FFFFFF;
            border-radius: 16px 16px 0 0;
            padding: 0.78rem 0.95rem;
            font-family: 'Sora', sans-serif;
            font-size: 0.84rem;
            font-weight: 800;
            letter-spacing: 0.05em;
            text-transform: none;
            font-variant-caps: all-small-caps;
            text-align: center;
            margin-bottom: 0;
        }}

        .cm-table-panel-caption {{
            margin: 0 0 0.45rem 0;
            padding: 0.42rem 0.8rem 0.2rem 0.8rem;
            border-left: 1px solid var(--cm-border);
            border-right: 1px solid var(--cm-border);
            border-bottom: 1px solid var(--cm-border);
            border-radius: 0 0 14px 14px;
            background: rgba(255,255,255,0.72);
            color: var(--cm-muted);
            font-size: 0.84rem;
        }}

        .cm-analysis-hint-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.9rem;
            margin: 0.15rem 0 0.55rem 0;
        }}

        .cm-analysis-hint-text {{
            color: var(--cm-muted);
            font-size: 0.82rem;
            line-height: 1.35;
        }}

        .cm-analysis-jump-btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            white-space: nowrap;
            background: var(--cm-primary);
            color: #FFFFFF !important;
            text-decoration: none !important;
            padding: 0.52rem 0.8rem;
            border-radius: 999px;
            font-family: 'Sora', sans-serif;
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            font-variant-caps: all-small-caps;
            box-shadow: 0 10px 18px rgba(22, 58, 89, 0.18);
        }}

        .cm-mini-table-wrap {{
            background: rgba(255,255,255,0.8);
            border: 1px solid var(--cm-border);
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 10px 24px rgba(22, 58, 89, 0.06);
        }}

        .cm-mini-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.94rem;
        }}

        .cm-mini-table thead th {{
            background: var(--cm-primary);
            color: white;
            text-align: center;
            padding: 0.72rem 0.85rem;
            font-family: 'Sora', sans-serif;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: none;
            font-variant-caps: all-small-caps;
        }}

        .cm-mini-table td {{
            padding: 0.72rem 0.85rem;
            border-top: 1px solid rgba(22, 58, 89, 0.08);
            vertical-align: middle;
            color: var(--cm-text);
            text-align: center;
        }}

        .cm-mini-table tbody tr:nth-child(even) td {{
            background: rgba(221, 234, 248, 0.3);
        }}

        .cm-mini-table td.cm-number {{
            text-align: center;
            font-variant-numeric: tabular-nums;
            font-weight: 700;
        }}

        .cm-mini-table td.cm-number-soft {{
            text-align: center;
            font-variant-numeric: tabular-nums;
            font-weight: 500;
        }}

        .cm-analysis-main-wrap {{
            background: rgba(255,255,255,0.86);
            border: 1px solid var(--cm-border);
            border-radius: 20px;
            overflow: auto;
            box-shadow: 0 12px 28px rgba(22, 58, 89, 0.07);
        }}

        .cm-analysis-main-table {{
            width: max-content;
            min-width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 0.95rem;
        }}

        .cm-analysis-main-table thead th {{
            position: sticky;
            top: 0;
            z-index: 1;
            background: linear-gradient(135deg, var(--cm-primary), #245782);
            color: #FFFFFF;
            text-align: center;
            padding: 0.86rem 0.95rem;
            font-family: 'Sora', sans-serif;
            font-size: 0.82rem;
            font-weight: 800;
            letter-spacing: 0.03em;
            text-transform: none;
            font-variant-caps: all-small-caps;
            white-space: nowrap;
        }}

        .cm-analysis-main-table tbody td {{
            padding: 0.82rem 0.95rem;
            border-top: 1px solid rgba(22, 58, 89, 0.08);
            vertical-align: middle;
            color: var(--cm-text);
            white-space: nowrap;
            background: rgba(255,255,255,0.98);
            text-align: center;
        }}

        .cm-analysis-main-table tbody tr:nth-child(even) td {{
            background: rgba(237, 244, 252, 0.92);
        }}

        .cm-analysis-main-table tbody tr:hover td {{
            background: rgba(226, 237, 249, 0.96);
        }}

        .cm-analysis-main-table tbody tr.cm-row-selected td {{
            background: rgba(221, 234, 248, 0.98) !important;
            color: var(--cm-primary);
            font-weight: 700;
        }}

        .cm-analysis-main-table tbody td.cm-number {{
            text-align: center;
            font-variant-numeric: tabular-nums;
            font-weight: 700;
        }}

        .cm-analysis-main-table tbody td.cm-first-col {{
            font-weight: 800;
            color: var(--cm-primary);
            text-align: center;
        }}


        .cm-analysis-main-table thead th.cm-calculated-col {{
            background: linear-gradient(135deg, #7A5A00, #A97610);
            color: #FFFFFF;
        }}

        .cm-analysis-main-table tbody td.cm-calculated-col {{
            background: rgba(255, 244, 214, 0.96);
            color: #7A5A00;
            font-weight: 600;
        }}

        .cm-analysis-params {{
            background: rgba(255,255,255,0.72);
            border: 1px solid var(--cm-border);
            border-radius: 18px;
            padding: 0.65rem 0.8rem 0.2rem 0.8rem;
            box-shadow: 0 10px 24px rgba(22, 58, 89, 0.04);
            margin-bottom: 0.9rem;
        }}

        .cm-analysis-mode-shell {{
            margin: 0.2rem 0 0.35rem 0;
            padding: 0.85rem 1rem 0.15rem 1rem;
            border-radius: 18px;
            border: 1px solid rgba(22, 58, 89, 0.16);
            background: linear-gradient(180deg, rgba(221, 234, 248, 0.88), rgba(237, 244, 252, 0.78));
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.65);
        }}

        .cm-analysis-mode-kicker {{
            font-family: 'Sora', sans-serif;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #2F6B9E;
            margin-bottom: 0.12rem;
        }}

        .cm-analysis-mode-title {{
            font-family: 'Montserrat', sans-serif;
            font-size: 1.05rem;
            font-weight: 800;
            color: var(--cm-primary);
            margin-bottom: 0.12rem;
        }}

        .cm-analysis-mode-note {{
            font-size: 0.92rem;
            color: var(--cm-muted);
            margin-bottom: 0.35rem;
        }}

        .cm-badge {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.28rem 0.62rem;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 800;
            line-height: 1.1;
            white-space: nowrap;
        }}

        .cm-data-table-wrap {{
            background: rgba(255,255,255,0.88);
            border: 1px solid var(--cm-border);
            border-radius: 18px;
            overflow: auto;
            box-shadow: 0 10px 24px rgba(22, 58, 89, 0.06);
        }}

        .cm-data-table {{
            width: 100%;
            min-width: 980px;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 0.93rem;
        }}

        .cm-data-table thead th {{
            position: sticky;
            top: 0;
            z-index: 2;
            background: linear-gradient(135deg, var(--cm-primary), #245782);
            color: #FFFFFF;
            text-align: left;
            padding: 0.82rem 0.9rem;
            font-family: 'Sora', sans-serif;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            white-space: nowrap;
        }}

        .cm-data-table thead th:first-child {{
            border-top-left-radius: 16px;
        }}

        .cm-data-table thead th:last-child {{
            border-top-right-radius: 16px;
        }}

        .cm-data-table tbody td {{
            padding: 0.78rem 0.9rem;
            border-top: 1px solid rgba(22, 58, 89, 0.08);
            vertical-align: middle;
            color: var(--cm-text);
            background: rgba(255,255,255,0.96);
            white-space: nowrap;
        }}

        .cm-data-table tbody tr:nth-child(even) td {{
            background: rgba(221, 234, 248, 0.28);
        }}

        .cm-data-table td.cm-number {{
            text-align: right;
            font-variant-numeric: tabular-nums;
            font-weight: 700;
        }}

        .cm-data-table td.cm-strong {{
            font-weight: 700;
            color: var(--cm-primary);
            white-space: normal;
            min-width: 240px;
        }}

        .cm-data-table td.cm-wrap {{
            white-space: normal;
        }}

        .cm-data-table td.cm-narrow {{
            width: 1%;
        }}

        .cm-siren-link {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            font-weight: 800;
            color: var(--cm-primary) !important;
            text-decoration: none;
            border-bottom: 2px solid rgba(22,58,89,0.18);
            padding-bottom: 0.05rem;
        }}

        .cm-siren-link:hover {{
            color: #245782 !important;
            border-bottom-color: #245782;
        }}

        .cm-siren-link span {{
            font-size: 0.85rem;
            opacity: 0.88;
        }}

        .cm-stream-note {{
            margin: 0.1rem 0 0.65rem 0;
            color: var(--cm-muted);
            font-size: 0.86rem;
            font-weight: 600;
        }}

        .cm-stream-head {{
            background: linear-gradient(135deg, var(--cm-primary), #245782);
            color: #FFFFFF;
            border-radius: 14px;
            padding: 0.72rem 0.8rem;
            font-family: 'Sora', sans-serif;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            min-height: 48px;
            display: flex;
            align-items: center;
            box-shadow: 0 10px 18px rgba(22, 58, 89, 0.10);
        }}

        .cm-stream-cell {{
            background: rgba(255,255,255,0.90);
            border: 1px solid rgba(22, 58, 89, 0.09);
            border-radius: 14px;
            padding: 0.7rem 0.8rem;
            min-height: 52px;
            display: flex;
            align-items: center;
            color: var(--cm-text);
            box-shadow: 0 6px 14px rgba(22, 58, 89, 0.04);
            font-size: 0.93rem;
        }}

        .cm-stream-cell.cm-even {{
            background: rgba(238, 245, 253, 0.92);
        }}

        .cm-stream-cell.cm-number {{
            justify-content: flex-end;
            font-variant-numeric: tabular-nums;
            font-weight: 700;
        }}

        .cm-stream-cell.cm-text-strong {{
            font-weight: 700;
            color: var(--cm-primary);
        }}

        .cm-hero-pills {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin-top: 1rem;
        }}

        .cm-hero-pill {{
            padding: 0.45rem 0.75rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.10);
            border: 1px solid rgba(255,255,255,0.16);
            color: rgba(255,255,255,0.95);
            font-size: 0.86rem;
            font-weight: 700;
        }}

        .cm-premium-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 1rem;
            margin: 1rem 0 1.2rem 0;
        }}

        .cm-premium-card {{
            position: relative;
            overflow: hidden;
            border-radius: 24px;
            padding: 1.15rem 1.15rem 1rem 1.15rem;
            background: linear-gradient(160deg, rgba(22, 58, 89, 0.98), rgba(36, 87, 130, 0.92));
            border: 1px solid rgba(255,255,255,0.08);
            color: #FFFFFF;
            min-height: 190px;
            box-shadow: 0 14px 34px rgba(22, 58, 89, 0.16);
        }}

        .cm-premium-card::after {{
            content: "";
            position: absolute;
            right: -42px;
            top: -42px;
            width: 128px;
            height: 128px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,255,255,0.18), rgba(255,255,255,0));
        }}

        .cm-premium-kicker {{
            font-family: 'Sora', sans-serif;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: rgba(255,255,255,0.76);
        }}

        .cm-premium-title {{
            margin-top: 0.4rem;
            font-family: 'Sora', sans-serif;
            font-size: 1.12rem;
            font-weight: 800;
            line-height: 1.2;
            color: #FFFFFF;
        }}

        .cm-premium-value {{
            margin-top: 0.7rem;
            font-family: 'Montserrat', sans-serif;
            font-size: 1.72rem;
            font-weight: 800;
            color: #FFFFFF;
        }}

        .cm-premium-text {{
            margin-top: 0.45rem;
            font-size: 0.95rem;
            line-height: 1.55;
            color: rgba(255,255,255,0.84);
        }}

        .cm-page-hero {{
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 0 1.25rem 0;
            padding: 0.25rem 0 0.5rem 0;
        }}

        .cm-page-hero-inner {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            width: 100%;
        }}

        .cm-page-hero-logo {{
            width: 74px;
            height: 74px;
            object-fit: contain;
            filter: drop-shadow(0 10px 18px rgba(22, 58, 89, 0.16));
        }}

        .cm-page-hero-title {{
            margin: 0;
            font-family: 'Cormorant Garamond', serif !important;
            font-size: clamp(2.2rem, 4vw, 3.5rem);
            font-weight: 700;
            line-height: 1;
            letter-spacing: 0.01em;
            color: var(--cm-primary);
        }}

        @media (max-width: 900px) {{
            .cm-page-hero-inner {{
                flex-direction: column;
                gap: 0.55rem;
            }}
            .cm-page-hero-logo {{
                width: 58px;
                height: 58px;
            }}
            .cm-page-hero-title {{
                text-align: center;
            }}
            .cm-premium-grid {{
                grid-template-columns: 1fr;
            }}
            .cm-hero-grid {{
                grid-template-columns: 1fr;
            }}
            .cm-hero-logo-card {{
                min-height: 140px;
            }}
            .cm-sidebar-brand img {{
                width: 52px;
                height: 52px;
            }}
        }}

        .cm-client-toolbar {{
            display: flex;
            align-items: end;
            gap: 0.8rem;
            flex-wrap: wrap;
            margin-bottom: 0.8rem;
        }}

        .cm-client-breadcrumb {{
            font-size: 0.88rem;
            color: var(--cm-muted);
            margin-bottom: 0.4rem;
        }}

        .cm-client-hero {{
            background: linear-gradient(145deg, rgba(22, 58, 89, 0.98), rgba(36, 87, 130, 0.93));
            border-radius: 24px;
            padding: 1.15rem 1.2rem 1rem 1.2rem;
            color: #FFFFFF;
            box-shadow: 0 16px 36px rgba(22, 58, 89, 0.16);
            margin-bottom: 1rem;
        }}

        .cm-client-title-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            flex-wrap: wrap;
        }}

        .cm-client-title {{
            font-family: 'Sora', sans-serif;
            font-size: 1.85rem;
            font-weight: 800;
            line-height: 1.1;
            color: #FFFFFF;
        }}

        .cm-client-subtitle {{
            margin-top: 0.35rem;
            color: rgba(255,255,255,0.86);
            font-size: 0.98rem;
            font-weight: 600;
        }}

        .cm-client-badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin-top: 0.95rem;
        }}

        .cm-client-hero-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.8rem;
            margin-top: 1rem;
        }}

        .cm-client-hero-card {{
            background: rgba(255,255,255,0.10);
            border: 1px solid rgba(255,255,255,0.14);
            border-radius: 18px;
            padding: 0.8rem 0.9rem;
            min-height: 92px;
        }}

        .cm-client-hero-label {{
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            color: rgba(255,255,255,0.72);
            margin-bottom: 0.4rem;
        }}

        .cm-client-hero-value {{
            font-family: 'Sora', sans-serif;
            font-size: 1rem;
            font-weight: 700;
            color: #FFFFFF;
            line-height: 1.28;
        }}

        .cm-client-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.8rem;
            margin: 0.35rem 0 1rem 0;
        }}

        .cm-client-field {{
            background: rgba(255,255,255,0.84);
            border: 1px solid var(--cm-border);
            border-radius: 18px;
            padding: 0.9rem 0.95rem;
            box-shadow: 0 10px 22px rgba(22, 58, 89, 0.05);
            min-height: 98px;
        }}

        .cm-client-field-label {{
            color: var(--cm-muted);
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: 0.4rem;
        }}

        .cm-client-field-value {{
            color: var(--cm-text);
            font-size: 1rem;
            font-weight: 700;
            line-height: 1.35;
            white-space: pre-wrap;
            word-break: break-word;
        }}

        .cm-empty-note {{
            background: rgba(255,255,255,0.84);
            border: 1px dashed rgba(22, 58, 89, 0.22);
            border-radius: 18px;
            padding: 1rem 1rem;
            color: var(--cm-muted);
        }}

        .cm-click-table-wrap {{
            overflow: auto;
            border: 1px solid rgba(22, 58, 89, 0.12);
            border-radius: 18px;
            background: rgba(255,255,255,0.92);
            box-shadow: 0 10px 24px rgba(22, 58, 89, 0.06);
        }}

        .cm-click-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            min-width: 880px;
        }}

        .cm-click-table thead th {{
            position: sticky;
            top: 0;
            z-index: 1;
            background: var(--cm-primary);
            color: white;
            font-family: 'Sora', sans-serif;
            font-size: 0.86rem;
            font-weight: 700;
            letter-spacing: 0.01em;
            padding: 0.78rem 0.9rem;
            text-align: center;
            text-transform: none;
            font-variant-caps: all-small-caps;
            white-space: nowrap;
        }}

        .cm-click-table tbody td {{
            padding: 0.72rem 0.9rem;
            border-bottom: 1px solid rgba(22, 58, 89, 0.08);
            vertical-align: middle;
            background: rgba(255,255,255,0.98);
            white-space: nowrap;
            text-align: center;
        }}

        .cm-click-table tbody tr:nth-child(even) td {{
            background: rgba(244, 249, 255, 0.96);
        }}

        .cm-click-table tbody tr:hover td {{
            background: rgba(231, 241, 252, 0.96);
        }}

        .cm-table-link {{
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
            color: var(--cm-primary) !important;
            font-weight: 800;
            text-decoration: none;
            border-bottom: 1px solid rgba(22, 58, 89, 0.24);
            padding-bottom: 1px;
            cursor: pointer;
        }}

        .cm-table-link:hover {{
            color: var(--cm-secondary) !important;
            border-bottom-color: rgba(42, 108, 168, 0.42);
        }}

        .cm-table-link-icon {{
            font-size: 0.78rem;
            opacity: 0.8;
        }}

        @media (max-width: 1200px) {{
            .cm-client-hero-grid, .cm-client-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
        }}

        @media (max-width: 780px) {{
            .cm-premium-grid, .cm-client-hero-grid, .cm-client-grid {{
                grid-template-columns: 1fr;
            }}
        }}


        div[data-testid="stRadio"] {{
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
            border: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
        }}

        div[data-testid="stRadio"] > div {{
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
            border: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
        }}

        div[data-testid="stRadio"] fieldset {{
            margin: 0 !important;
            padding: 0 !important;
            border: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
            min-width: 0 !important;
        }}

        div[data-testid="stRadio"] hr {{
            display: none !important;
        }}
        
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand(user: dict | None = None) -> None:
    with st.sidebar:
        st.markdown(
            f"""
            <div class="cm-sidebar-brand">
                <img src="{LOGO_DATA_URI}" alt="Logo Classification Management" />
                <div>
                    <div class="cm-sidebar-brand-title">CLASSIFICATION<br/>MANAGEMENT</div>
                    <div class="cm-sidebar-brand-subtitle">Portefeuille & gouvernance des risques</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if user is not None:
            st.caption(f"Connecté en tant que {user['display_name']}")



def render_home_hero(title: str) -> None:
    st.markdown(
        f'''
        <section class="cm-page-hero">
            <div class="cm-page-hero-inner">
                <img class="cm-page-hero-logo" src="{LOGO_DATA_URI}" alt="Logo Classification Management" />
                <h1 class="cm-page-hero-title">{escape(title)}</h1>
            </div>
        </section>
        ''',
        unsafe_allow_html=True,
    )


def render_home_showcase(user: dict | None = None) -> None:
    manifest = load_manifest() if user else None

    if user is None:
        cards = [
            {
                "kicker": "Supervision",
                "title": "Vision portefeuille",
                "value": "360°",
                "text": "Consolidez le portefeuille, visualisez les vigilances et priorisez les dossiers les plus sensibles.",
                "foot": "Tableau de bord unifié",
            },
            {
                "kicker": "Administration",
                "title": "Publication contrôlée",
                "value": "01 / 02 / 03",
                "text": "L’administrateur charge un jeu de données unique puis l’ensemble des utilisateurs travaille sur la même version active.",
                "foot": "Un seul jeu partagé",
            },
            {
                "kicker": "Multi-société",
                "title": "Accès cloisonnés",
                "value": "Users",
                "text": "Chaque utilisateur n’accède qu’à son périmètre autorisé, avec une expérience fluide et homogène.",
                "foot": "Gouvernance d’accès intégrée",
            },
        ]
    else:
        if user["role"] == "admin" or "ALL" in user["societes_autorisees"]:
            scope_value = "Toutes"
            scope_text = "Vous pouvez superviser l’ensemble des sociétés présentes dans le jeu actif."
        else:
            scope_value = str(len(user["societes_autorisees"]))
            scope_text = "Votre périmètre est limité aux sociétés autorisées sur votre compte."
        published_value = format_manifest_date(manifest.get("published_at_utc")) if manifest else "En attente"
        published_text = (
            "Jeu actif publié par {}.".format(manifest.get("published_by_name") or manifest.get("published_by") or "inconnu")
            if manifest else
            "Aucun jeu de données n’a encore été publié."
        )
        cards = [
            {
                "kicker": "Périmètre",
                "title": "Accès utilisateur",
                "value": scope_value,
                "text": scope_text,
                "foot": f"Rôle : {user['role']}",
            },
            {
                "kicker": "Jeu actif",
                "title": "Publication données",
                "value": published_value,
                "text": published_text,
                "foot": (
                    "Sociétés : {}".format(manifest.get("societes_count", 0))
                    if manifest else "Publication requise"
                ),
            },
            {
                "kicker": "Gouvernance",
                "title": "Cadre de pilotage",
                "value": "V / R",
                "text": "Le bleu structure la navigation, le rouge marque le critique ou le risque avéré, l’orange signale le niveau élevé.",
                "foot": "Lecture visuelle harmonisée",
            },
        ]

    html = ['<div class="cm-premium-grid">']
    for card in cards:
        html.append(
            (
                f'<div class="cm-premium-card">'
                f'<div class="cm-premium-kicker">{escape(card["kicker"])}</div>'
                f'<div class="cm-premium-title">{escape(card["title"])}</div>'
                f'<div class="cm-premium-value">{escape(card["value"])}</div>'
                f'<div class="cm-premium-text">{escape(card["text"])}</div>'
                f'<div class="cm-premium-foot">{escape(card["foot"])}</div>'
                f'</div>'
            )
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def app_root() -> Path:
    return Path(__file__).resolve().parent


def storage_root() -> Path:
    root = app_root() / STORAGE_ROOT
    root.mkdir(parents=True, exist_ok=True)
    return root


def active_dataset_path() -> Path:
    return storage_root() / ACTIVE_DATASET_DIR


def manifest_path() -> Path:
    return active_dataset_path() / MANIFEST_FILE


def review_simulations_path() -> Path:
    return active_dataset_path() / REVIEW_SIMULATIONS_FILE


def review_simulation_pdfs_path() -> Path:
    path = active_dataset_path() / REVIEW_SIM_PDF_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename_component(value: object, fallback: str = "document") -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    return text or fallback


def review_simulation_pdf_storage_name(row: pd.Series) -> str:
    soc = safe_filename_component(row.get(SOC_COL, ""), fallback="societe")
    siren = safe_filename_component(row.get("SIREN", ""), fallback="siren")
    return f"revue_simulation_{soc}_{siren}.pdf"


def review_simulation_pdf_download_name(row: pd.Series) -> str:
    siren = safe_filename_component(row.get("SIREN", ""), fallback="siren")
    denomination = safe_filename_component(row.get("Dénomination", ""), fallback="dossier")
    return f"revue_simulation_{siren}_{denomination}.pdf"


def review_simulation_pdf_path(row: pd.Series) -> Path:
    return review_simulation_pdfs_path() / review_simulation_pdf_storage_name(row)


def review_simulation_classification_pdf_storage_name(row: pd.Series) -> str:
    soc = safe_filename_component(row.get(SOC_COL, ""), fallback="societe")
    siren = safe_filename_component(row.get("SIREN", ""), fallback="siren")
    return f"{CLASSIFICATION_PDF_PREFIX}_{soc}_{siren}.pdf"


def review_simulation_classification_pdf_download_name(row: pd.Series) -> str:
    siren = safe_filename_component(row.get("SIREN", ""), fallback="siren")
    denomination = safe_filename_component(row.get("Dénomination", ""), fallback="dossier")
    return f"{CLASSIFICATION_PDF_PREFIX}_{siren}_{denomination}.pdf"


def review_simulation_classification_pdf_path(row: pd.Series) -> Path:
    return review_simulation_pdfs_path() / review_simulation_classification_pdf_storage_name(row)


def review_simulation_pdf_entries_for_row(row: pd.Series) -> list[dict[str, object]]:
    base_label = f"{row.get('SIREN', '')} - {row.get('Dénomination', '')}"
    return [
        {
            "kind": "review",
            "path": review_simulation_pdf_path(row),
            "label": f"{base_label} - Revue & Simulation",
            "download_name": review_simulation_pdf_download_name(row),
        },
        {
            "kind": "classification",
            "path": review_simulation_classification_pdf_path(row),
            "label": f"{base_label} - Classification",
            "download_name": review_simulation_classification_pdf_download_name(row),
        },
    ]


def find_file(filename: str) -> Path:
    here = app_root()
    candidates = [
        here / filename,
        here / "data" / filename,
        Path.cwd() / filename,
        Path.cwd() / "data" / filename,
    ]
    for path in candidates:
        if path.exists():
            return path
    searched = "\n - ".join(str(p) for p in candidates)
    raise FileNotFoundError(f"Impossible de trouver {filename}. Emplacements testés :\n - {searched}")


def read_csv_semicolon(source) -> pd.DataFrame:
    return pd.read_csv(source, sep=";", encoding="utf-8-sig").dropna(how="all")


def normalize_siren(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.strip()
        .str.replace(r"\\.0$", "", regex=True)
        .replace({"nan": np.nan, "None": np.nan, "": np.nan})
    )


def normalize_societe_id(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.strip()
        .str.upper()
        .replace({"nan": np.nan, "None": np.nan, "": np.nan})
    )


def clean_text_column(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .str.strip()
        .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
        .astype("string")
    )


def parse_percent(value):
    if pd.isna(value):
        return np.nan
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("%", "").replace(",", ".")
    if text == "":
        return np.nan
    try:
        return float(text) / 100.0
    except ValueError:
        return np.nan


def validate_required_columns(df: pd.DataFrame, label: str) -> None:
    missing = [col for col in REQUIRED_COLUMNS[label] if col not in df.columns]
    if missing:
        raise DataValidationError(
            f"Le fichier '{DATA_FILES.get(label, USERS_FILE)}' ne contient pas les colonnes obligatoires : {', '.join(missing)}. "
            f"Ajoutez notamment '{SOC_COL}' en première colonne dans 01, 02 et 03."
        )


def load_users() -> pd.DataFrame:
    users = read_csv_semicolon(find_file(USERS_FILE))
    validate_required_columns(users, "users")
    users["username"] = users["username"].astype(str).str.strip().str.lower()
    users["password"] = users["password"].fillna("").astype(str)
    users["role"] = users["role"].astype(str).str.strip().str.lower()
    users["enabled"] = users["enabled"].astype(str).str.strip().str.lower().isin(["true", "1", "oui", "yes"])
    users["societes_autorisees"] = users["societes_autorisees"].fillna("").astype(str)
    if "display_name" not in users.columns:
        users["display_name"] = users["username"]
    else:
        users["display_name"] = users["display_name"].fillna(users["username"]).astype(str).str.strip()
        users.loc[users["display_name"].eq(""), "display_name"] = users["username"]
    return users


def parse_allowed_societies(raw_value: str) -> list[str]:
    raw = str(raw_value or "").strip()
    if not raw:
        return []
    if raw.upper() == "ALL":
        return ["ALL"]
    return sorted({item.strip().upper() for item in raw.split(",") if item.strip()})


def authenticate_user(username: str, password: str):
    users = load_users()
    username = str(username or "").strip().lower()
    row = users.loc[users["username"] == username]
    if row.empty:
        return None
    user = row.iloc[0]
    if not bool(user["enabled"]):
        return None
    if not hmac.compare_digest(str(password or ""), str(user["password"] or "")):
        return None
    return {
        "username": str(user["username"]),
        "display_name": str(user["display_name"]),
        "role": str(user["role"]),
        "societes_autorisees": parse_allowed_societies(user["societes_autorisees"]),
    }


def get_current_user():
    return st.session_state.get("authenticated_user")


def login_form() -> None:
    render_home_hero("Classification Management")
    render_home_showcase(None)
    st.markdown('<h3 class="cm-section-title">Connexion</h3>', unsafe_allow_html=True)
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Identifiant")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter", type="primary")

    if submitted:
        user = authenticate_user(username, password)
        if user is None:
            st.error("Identifiants invalides ou compte désactivé.")
        else:
            st.session_state["authenticated_user"] = user
            st.rerun()

    st.markdown('<div class="cm-home-link">www.beclm.com</div>', unsafe_allow_html=True)


def logout_button() -> None:
    if st.button("Se déconnecter"):
        st.session_state.pop("authenticated_user", None)
        st.rerun()


def parse_uploaded_dataset(uploaded_files: dict[str, object]) -> dict[str, pd.DataFrame]:
    parsed: dict[str, pd.DataFrame] = {}
    for label, expected_name in DATA_FILES.items():
        uploaded = uploaded_files.get(label)
        if uploaded is None:
            raise DataValidationError(f"Chargez le fichier {expected_name}.")
        df = read_csv_semicolon(BytesIO(uploaded.getvalue()))
        validate_required_columns(df, label)
        df[SOC_COL] = normalize_societe_id(df[SOC_COL])
        df["SIREN"] = normalize_siren(df["SIREN"])
        df = df.dropna(subset=KEY_COLUMNS).copy()
        if df.empty:
            raise DataValidationError(f"Le fichier {expected_name} ne contient aucune ligne exploitable après normalisation.")
        parsed[label] = df
    return parsed


def write_manifest(parsed: dict[str, pd.DataFrame], user: dict) -> dict:
    all_societies = sorted(
        {
            str(v).strip().upper()
            for df in parsed.values()
            for v in df[SOC_COL].dropna().astype(str)
            if str(v).strip()
        }
    )
    return {
        "published_at_utc": datetime.now(timezone.utc).isoformat(),
        "published_by": user["username"],
        "published_by_name": user["display_name"],
        "files": {label: DATA_FILES[label] for label in DATA_FILES},
        "row_counts": {label: int(len(df)) for label, df in parsed.items()},
        "societes": all_societies,
        "societes_count": len(all_societies),
    }


def publish_uploaded_dataset(uploaded_files: dict[str, object], user: dict) -> None:
    parsed = parse_uploaded_dataset(uploaded_files)

    root = storage_root()
    temp_dir = root / f"_tmp_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    current_dir = active_dataset_path()
    backup_dir = root / "_backup_active"

    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    temp_dir.mkdir(parents=True, exist_ok=False)

    try:
        for label, expected_name in DATA_FILES.items():
            uploaded = uploaded_files[label]
            (temp_dir / expected_name).write_bytes(uploaded.getvalue())

        manifest = write_manifest(parsed, user)
        (temp_dir / MANIFEST_FILE).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        if current_dir.exists():
            current_dir.replace(backup_dir)
        temp_dir.replace(current_dir)
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
    except Exception:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        if backup_dir.exists() and not current_dir.exists():
            backup_dir.replace(current_dir)
        raise


def clear_published_dataset() -> None:
    current_dir = active_dataset_path()
    if current_dir.exists():
        shutil.rmtree(current_dir)


def load_manifest() -> dict | None:
    path = manifest_path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_manifest(manifest: dict) -> None:
    manifest_path().write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def load_saved_review_planning_settings() -> tuple[dict[str, int], dict[str, int]]:
    manifest = load_manifest() or {}
    saved = manifest.get("review_planning_settings") or {}
    saved_freq = saved.get("frequencies_months") or {}
    saved_cap = saved.get("capacity_per_month") or {}

    freq_map: dict[str, int] = {}
    cap_map: dict[str, int] = {}
    for label in VIGILANCE_ORDER:
        try:
            freq_map[label] = max(int(saved_freq.get(label, REVIEW_FREQUENCY_DEFAULTS.get(label, 12))), 1)
        except Exception:
            freq_map[label] = int(REVIEW_FREQUENCY_DEFAULTS.get(label, 12))
        try:
            cap_map[label] = max(int(saved_cap.get(label, REVIEW_CAPACITY_DEFAULTS.get(label, 10))), 1)
        except Exception:
            cap_map[label] = int(REVIEW_CAPACITY_DEFAULTS.get(label, 10))
    return freq_map, cap_map


def persist_review_planning_settings(freq_map: dict[str, int], cap_map: dict[str, int], user: dict | None = None) -> None:
    manifest = load_manifest() or {}
    manifest["review_planning_settings"] = {
        "frequencies_months": {label: int(freq_map.get(label, REVIEW_FREQUENCY_DEFAULTS.get(label, 12))) for label in VIGILANCE_ORDER},
        "capacity_per_month": {label: int(cap_map.get(label, REVIEW_CAPACITY_DEFAULTS.get(label, 10))) for label in VIGILANCE_ORDER},
        "saved_at_utc": datetime.now(timezone.utc).isoformat(),
        "saved_by": (user or {}).get("username"),
        "saved_by_name": (user or {}).get("display_name"),
    }
    save_manifest(manifest)




def clear_review_simulation_ephemeral_state() -> None:
    st.session_state.pop(REVIEW_SIM_GEMINI_KEY_STATE, None)
    st.session_state.pop("review_sim_explain_target", None)
    st.session_state.pop("review_sim_last_cell_action", None)

def clear_ephemeral_state_if_view_changes(next_view: str) -> None:
    target_view = str(next_view or "").strip()
    current_view = str(st.session_state.get("cm_view", "portfolio") or "portfolio").strip()
    if current_view == "client":
        current_view = str(st.session_state.get("cm_previous_view", "portfolio") or "portfolio").strip()
    if target_view and current_view != target_view:
        clear_review_simulation_ephemeral_state()


def load_review_simulation_store() -> pd.DataFrame:
    path = review_simulations_path()
    legacy_est_label = "Statut de vigilance espéré après remédiation"
    columns = KEY_COLUMNS + [
        "Explique moi",
        REVIEW_SIM_EST_LABEL,
        REVIEW_SIM_AI_STRUCTURED_LABEL,
        "updated_at_utc",
    ]
    if not path.exists():
        return pd.DataFrame(columns=columns)
    try:
        df = read_csv_semicolon(path)
    except Exception:
        return pd.DataFrame(columns=columns)
    if legacy_est_label in df.columns and REVIEW_SIM_EST_LABEL not in df.columns:
        df[REVIEW_SIM_EST_LABEL] = df[legacy_est_label]
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    df[SOC_COL] = normalize_societe_id(df[SOC_COL])
    df["SIREN"] = normalize_siren(df["SIREN"])
    for col in ["Explique moi", REVIEW_SIM_EST_LABEL, REVIEW_SIM_AI_STRUCTURED_LABEL, "updated_at_utc"]:
        df[col] = df[col].fillna("").astype(str)
    return df[columns].dropna(subset=KEY_COLUMNS).drop_duplicates(subset=KEY_COLUMNS, keep="last")



def save_review_simulation_store(df: pd.DataFrame) -> None:
    path = review_simulations_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    save_df = df.copy()
    for col in KEY_COLUMNS + ["Explique moi", REVIEW_SIM_EST_LABEL, REVIEW_SIM_AI_STRUCTURED_LABEL, "updated_at_utc"]:
        if col not in save_df.columns:
            save_df[col] = ""
    save_df[SOC_COL] = normalize_societe_id(save_df[SOC_COL])
    save_df["SIREN"] = normalize_siren(save_df["SIREN"])
    save_df = save_df.dropna(subset=KEY_COLUMNS).drop_duplicates(subset=KEY_COLUMNS, keep="last")
    save_df.to_csv(path, sep=";", index=False, encoding="utf-8-sig")



def review_type_for_vigilance(vigilance: str) -> str:
    return REVIEW_TYPE_BY_VIGILANCE.get(str(vigilance or "").strip(), "Revue standard")



def review_objectives_for_vigilance(vigilance: str) -> tuple[str, str]:
    return REVIEW_OBJECTIVES_BY_VIGILANCE.get(
        str(vigilance or "").strip(),
        REVIEW_OBJECTIVES_BY_VIGILANCE["Vigilance Aucune"],
    )



def coerce_mixed_date(value) -> pd.Timestamp | pd.NaT:
    if value is None:
        return pd.NaT
    if isinstance(value, pd.Timestamp):
        return value
    if isinstance(value, str):
        text = value.strip().replace(" ", " ")
        if not text or text.lower() in {"nan", "nat", "none"}:
            return pd.NaT
        numeric_text = text.replace(",", ".")
        if re.fullmatch(r"\d+(?:\.\d+)?", numeric_text):
            try:
                numeric = float(numeric_text)
                if 20_000 <= numeric <= 60_000:
                    return pd.Timestamp("1899-12-30") + pd.to_timedelta(numeric, unit="D")
            except Exception:
                pass
        dt = pd.to_datetime(text, errors="coerce", dayfirst=True)
        if pd.isna(dt):
            dt = pd.to_datetime(text.replace('.', '/'), errors="coerce", dayfirst=True)
        return dt
    if isinstance(value, (int, float, np.integer, np.floating)):
        try:
            if pd.isna(value):
                return pd.NaT
        except Exception:
            pass
        numeric = float(value)
        if 20_000 <= numeric <= 60_000:
            return pd.Timestamp("1899-12-30") + pd.to_timedelta(numeric, unit="D")
        return pd.to_datetime(value, errors="coerce", dayfirst=True)
    return pd.to_datetime(value, errors="coerce", dayfirst=True)


def format_short_date(value) -> str:
    dt = coerce_mixed_date(value)
    if pd.isna(dt):
        return ""
    return pd.Timestamp(dt).strftime("%d/%m/%Y")



def prompt_json_value(value: object) -> object:
    if isinstance(value, dict):
        return {str(k): prompt_json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [prompt_json_value(v) for v in value]
    if value is None:
        return None
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, (pd.Timestamp, datetime)):
        if pd.isna(value):
            return None
        ts = pd.Timestamp(value)
        return ts.strftime("%Y-%m-%d") if ts.time() == datetime.min.time() else ts.isoformat()
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    if isinstance(value, str):
        compact = re.sub(r"\s+", " ", value).strip()
        return compact or None
    return value



def row_payload_from_prefix(row: pd.Series, prefix: str) -> dict[str, object]:
    payload: dict[str, object] = {}
    for col in row.index:
        name = str(col)
        if not name.startswith(prefix):
            continue
        payload[name[len(prefix):]] = prompt_json_value(row.get(col))
    return payload



def row_payload_from_columns(row: pd.Series, columns: list[str]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for col in columns:
        if col in row.index:
            payload[str(col)] = prompt_json_value(row.get(col))
    return payload


def grouped_indicators_payload(indicators_payload: dict[str, object]) -> list[dict[str, object]]:
    if not indicators_payload:
        return []
    groups = indicator_group_map(list(indicators_payload.keys()))
    grouped: list[dict[str, object]] = []
    for indicator_name, mapping in groups.items():
        item_payload: dict[str, object] = {}
        for field_label, raw_col in mapping.items():
            item_payload[field_label] = prompt_json_value(indicators_payload.get(raw_col))
        if not any(value not in (None, "", [], {}) for value in item_payload.values()):
            continue
        grouped.append({"nom_indicateur": indicator_name, "donnees": item_payload})
    grouped.sort(key=lambda item: normalize_text_for_matching(item.get("nom_indicateur", "")))
    return grouped


def available_indicator_names_from_row(row: pd.Series) -> list[str]:
    indicators_payload = row_payload_from_prefix(row, GEMINI_INDICATORS_SOURCE_PREFIX)
    return [str(item.get("nom_indicateur", "") or "").strip() for item in grouped_indicators_payload(indicators_payload) if str(item.get("nom_indicateur", "") or "").strip()]



def indicator_reference_key(value: object) -> str:
    return normalize_text_for_matching(value)


def indicator_reference_default_df() -> pd.DataFrame:
    return pd.DataFrame(list(DEFAULT_INDICATOR_REFERENCE_ROWS), columns=INDICATOR_REFERENCE_COLUMNS)


def sanitize_indicator_reference_df(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None:
        return indicator_reference_default_df().copy()
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)
    result = df.copy()
    for col in INDICATOR_REFERENCE_COLUMNS:
        if col not in result.columns:
            result[col] = ""
    result = result[INDICATOR_REFERENCE_COLUMNS].copy()
    for col in INDICATOR_REFERENCE_COLUMNS:
        result[col] = result[col].map(lambda value: "" if value is None or pd.isna(value) else str(value).strip())
    result = result[result["Indicateur d’alerte"].astype(str).str.strip().ne("")].reset_index(drop=True)
    return result


def merge_indicator_reference_with_hard_defaults(df: pd.DataFrame | None, prefer_loaded_for_known: bool = False) -> pd.DataFrame:
    baseline = sanitize_indicator_reference_df(indicator_reference_default_df())
    if df is None:
        return baseline
    loaded = sanitize_indicator_reference_df(df)
    if loaded.empty:
        return baseline

    baseline = baseline.assign(__key=baseline["Indicateur d’alerte"].map(indicator_reference_key))
    loaded = loaded.assign(__key=loaded["Indicateur d’alerte"].map(indicator_reference_key))

    if prefer_loaded_for_known:
        merged = baseline.set_index("__key")
        for _, record in loaded.iterrows():
            key = str(record.get("__key", "") or "").strip()
            if not key:
                continue
            merged.loc[key, INDICATOR_REFERENCE_COLUMNS] = [record.get(col, "") for col in INDICATOR_REFERENCE_COLUMNS]
        result = merged.reset_index(drop=True)[INDICATOR_REFERENCE_COLUMNS]
        return sanitize_indicator_reference_df(result)

    baseline_keys = set(baseline["__key"].tolist())
    extra_rows = loaded[~loaded["__key"].isin(baseline_keys)].copy()
    if extra_rows.empty:
        return baseline[INDICATOR_REFERENCE_COLUMNS].reset_index(drop=True)
    result = pd.concat([baseline[INDICATOR_REFERENCE_COLUMNS], extra_rows[INDICATOR_REFERENCE_COLUMNS]], ignore_index=True)
    return sanitize_indicator_reference_df(result)


@st.cache_data(show_spinner=False)
def load_indicator_reference_seed() -> tuple[pd.DataFrame, str]:
    roots: list[Path] = []
    try:
        roots.append(Path(__file__).resolve().parent)
    except Exception:
        pass
    roots.extend([Path.cwd(), Path("/mnt/data")])

    seen: set[str] = set()
    for root in roots:
        for filename in INDICATOR_REFERENCE_FILENAME_CANDIDATES:
            candidate = root / filename
            candidate_key = str(candidate.absolute())
            if candidate_key in seen:
                continue
            seen.add(candidate_key)
            if not candidate.exists():
                continue
            try:
                loaded = pd.read_excel(candidate, dtype=str)
                merged = merge_indicator_reference_with_hard_defaults(loaded)
                if not merged.empty:
                    return merged, (
                        f"{INDICATOR_REFERENCE_DEFAULT_SOURCE_LABEL} Socle imposé, complété le cas échéant par des indicateurs supplémentaires issus de {candidate.name}."
                    )
            except Exception:
                continue

    return indicator_reference_default_df(), INDICATOR_REFERENCE_DEFAULT_SOURCE_LABEL


def ensure_review_simulation_indicator_reference_state() -> None:
    if REVIEW_SIM_INDICATOR_REFERENCE_STATE not in st.session_state:
        seed_df, source_label = load_indicator_reference_seed()
        st.session_state[REVIEW_SIM_INDICATOR_REFERENCE_STATE] = sanitize_indicator_reference_df(seed_df)
        st.session_state[REVIEW_SIM_INDICATOR_REFERENCE_SOURCE_STATE] = str(source_label)
    else:
        current_df = sanitize_indicator_reference_df(pd.DataFrame(st.session_state[REVIEW_SIM_INDICATOR_REFERENCE_STATE]))
        st.session_state[REVIEW_SIM_INDICATOR_REFERENCE_STATE] = merge_indicator_reference_with_hard_defaults(current_df, prefer_loaded_for_known=True)
        st.session_state.setdefault(REVIEW_SIM_INDICATOR_REFERENCE_SOURCE_STATE, INDICATOR_REFERENCE_DEFAULT_SOURCE_LABEL)


def get_review_simulation_indicator_reference_df() -> pd.DataFrame:
    ensure_review_simulation_indicator_reference_state()
    return sanitize_indicator_reference_df(pd.DataFrame(st.session_state[REVIEW_SIM_INDICATOR_REFERENCE_STATE]))


def indicator_reference_map() -> dict[str, dict[str, str]]:
    reference_df = get_review_simulation_indicator_reference_df()
    mapping: dict[str, dict[str, str]] = {}
    for _, record in reference_df.iterrows():
        key = indicator_reference_key(record.get("Indicateur d’alerte"))
        if not key:
            continue
        mapping[key] = {
            "famille": str(record.get("Famille", "") or "").strip(),
            "nom_indicateur": str(record.get("Indicateur d’alerte", "") or "").strip(),
            "sens_metier": str(record.get("Sens métier de l’indicateur pour l’IA", "") or "").strip(),
        }
    return mapping


def build_indicator_reference_guardrails(indicator_names: list[str] | None = None) -> list[dict[str, object]]:
    reference = indicator_reference_map()
    if indicator_names:
        allowed = {indicator_reference_key(name) for name in indicator_names if str(name or "").strip()}
    else:
        allowed = set(reference.keys())
    guardrails: list[dict[str, object]] = []
    for key, item in reference.items():
        if allowed and key not in allowed:
            continue
        rules = INDICATOR_REFERENCE_STRICT_RULES.get(item["nom_indicateur"], {})
        guardrails.append(
            {
                "nom_indicateur": prompt_json_value(item["nom_indicateur"]),
                "must_include_any": prompt_json_value(rules.get("must_include_any", [])),
                "must_not_include": prompt_json_value(rules.get("must_not_include", [])),
                "limites_interpretation": prompt_json_value(INDICATOR_REFERENCE_INTERPRETATION_LIMITS.get(item["nom_indicateur"], "Les valeurs détaillées, seuils et paramétrages internes BeCLM ne sont pas communiqués ; raisonner à partir de la nature de l’alerte et rester prudent.")),
                "approche_due_diligence": prompt_json_value(INDICATOR_REFERENCE_DUE_DILIGENCE_GUIDANCE.get(item["nom_indicateur"], "Appliquer les meilleures pratiques de due diligence adaptées à la nature de l’alerte, de façon proportionnée, traçable et défendable.")),
            }
        )
    return guardrails


def build_indicator_reference_payload(indicator_names: list[str] | None = None) -> list[dict[str, object]]:
    reference_df = get_review_simulation_indicator_reference_df()
    if indicator_names:
        normalized_names = {
            indicator_reference_key(name)
            for name in indicator_names
            if str(name or "").strip()
        }
        if normalized_names:
            reference_df = reference_df[
                reference_df["Indicateur d’alerte"].map(indicator_reference_key).isin(normalized_names)
            ].reset_index(drop=True)

    payload: list[dict[str, object]] = []
    for _, record in reference_df.iterrows():
        indicator_name = str(record.get("Indicateur d’alerte", "") or "").strip()
        strict_rules = INDICATOR_REFERENCE_STRICT_RULES.get(indicator_name, {})
        payload.append(
            {
                "famille": prompt_json_value(record.get("Famille")),
                "nom_indicateur": prompt_json_value(indicator_name),
                "sens_metier": prompt_json_value(record.get("Sens métier de l’indicateur pour l’IA")),
                "regles_strictes": {
                    "must_include_any": prompt_json_value(strict_rules.get("must_include_any", [])),
                    "must_not_include": prompt_json_value(strict_rules.get("must_not_include", [])),
                },
                "limites_interpretation": prompt_json_value(INDICATOR_REFERENCE_INTERPRETATION_LIMITS.get(indicator_name, "Les valeurs détaillées, seuils et paramétrages internes BeCLM ne sont pas communiqués ; raisonner à partir de la nature de l’alerte et rester prudent.")),
                "approche_due_diligence": prompt_json_value(INDICATOR_REFERENCE_DUE_DILIGENCE_GUIDANCE.get(indicator_name, "Appliquer les meilleures pratiques de due diligence adaptées à la nature de l’alerte, de façon proportionnée, traçable et défendable.")),
            }
        )
    return payload


def build_gemini_source_payload(row: pd.Series) -> dict[str, object]:
    context_columns = [
        SOC_COL,
        "SIREN",
        "Dénomination",
        "Type de revue",
        REVIEW_SIM_REAL_LABEL,
        "Vigilance",
        "Risque",
        "Statut EDD",
        "Date dernière revue",
        "Date prochaine revue",
        "Alertes actives",
        "Motifs",
        "Nb historique",
        "Score priorité",
    ]
    base_source_payload = row_payload_from_prefix(row, GEMINI_BASE_SOURCE_PREFIX)
    if not base_source_payload:
        base_source_payload = row_payload_from_columns(
            row,
            [
                SOC_COL,
                "SIREN",
                "Dénomination",
                "Pays de résidence",
                "Segment",
                "Produit(service) principal",
                "Canal d’opérations principal 12 mois",
                "Statut EDD",
                "Flag justificatif complet",
                "Analyste",
                "Valideur",
                "Date dernière revue",
                "Date prochaine revue",
                "Risque",
            ],
        )
    indicators_source_payload = row_payload_from_prefix(row, GEMINI_INDICATORS_SOURCE_PREFIX)
    if not indicators_source_payload:
        indicators_source_payload = row_payload_from_columns(
            row,
            [
                SOC_COL,
                "SIREN",
                "Vigilance Date de mise à jour",
                "Cash intensité Statut",
                "Nb Risque avéré",
                "Nb Risque potentiel",
                "Nb Risque mitigé",
                "Nb Risque levé",
                "Nb Non calculable",
            ],
        )
    indicator_groups_payload = grouped_indicators_payload(indicators_source_payload)
    indicator_reference_payload = build_indicator_reference_payload(
        [str(item.get("nom_indicateur", "") or "").strip() for item in indicator_groups_payload]
    )
    active_indicator_names = [str(item.get("nom_indicateur", "") or "").strip() for item in indicator_groups_payload]
    return {
        "contexte_simulation": row_payload_from_columns(row, context_columns),
        "alertes_calculees": build_row_alert_labels(row),
        "donnees_base_source": base_source_payload,
        "indicateurs_source": indicators_source_payload,
        "indicateurs_source_groupes": indicator_groups_payload,
        "referentiel_indicateurs_actifs": indicator_reference_payload,
        "garde_fous_referentiel_globaux": prompt_json_value(INDICATOR_REFERENCE_GLOBAL_GUARDRAILS),
        "garde_fous_referentiel_indicateurs": build_indicator_reference_guardrails(active_indicator_names),
        "cadre_methodologique_beclm": prompt_json_value(BECLM_METHODOLOGY_FRAME),
    }



def build_review_simulation_source_dataset(
    portfolio_df: pd.DataFrame,
    base_source_df: pd.DataFrame,
    indicators_source_df: pd.DataFrame,
) -> pd.DataFrame:
    portfolio_source = portfolio_df.copy()
    portfolio_source[SOC_COL] = normalize_societe_id(portfolio_source[SOC_COL])
    portfolio_source["SIREN"] = normalize_siren(portfolio_source["SIREN"])

    base_source = base_source_df.copy()
    base_source[SOC_COL] = normalize_societe_id(base_source[SOC_COL])
    base_source["SIREN"] = normalize_siren(base_source["SIREN"])
    base_source = base_source.rename(
        columns={col: f"{GEMINI_BASE_SOURCE_PREFIX}{col}" for col in base_source.columns if col not in KEY_COLUMNS}
    )

    indicators_source = indicators_source_df.copy()
    indicators_source[SOC_COL] = normalize_societe_id(indicators_source[SOC_COL])
    indicators_source["SIREN"] = normalize_siren(indicators_source["SIREN"])
    indicators_source = indicators_source.rename(
        columns={col: f"{GEMINI_INDICATORS_SOURCE_PREFIX}{col}" for col in indicators_source.columns if col not in KEY_COLUMNS}
    )

    merged = portfolio_source.merge(base_source, how="left", on=KEY_COLUMNS)
    merged = merged.merge(indicators_source, how="left", on=KEY_COLUMNS)
    return merged



def build_row_alert_labels(row: pd.Series) -> list[str]:
    labels: list[str] = []
    if int(row.get("Alerte justificatif incomplet", 0) or 0) == 1:
        labels.append("Justificatifs incomplets")
    if int(row.get("Alerte sans prochaine revue", 0) or 0) == 1:
        labels.append("Sans prochaine revue")
    if int(row.get("Alerte revue trop ancienne", 0) or 0) == 1:
        labels.append("Revue trop ancienne")
    if int(row.get("Alerte cross-border élevé", 0) or 0) == 1:
        labels.append("Cross-border élevé")
    if int(row.get("Alerte cash intensité élevée", 0) or 0) == 1:
        labels.append("Cash intensité élevée")
    risk = str(row.get("Risque", "") or "").strip()
    if risk == "Risque avéré":
        labels.append("Risque avéré")
    elif risk == "Risque potentiel":
        labels.append("Risque potentiel")
    edd = str(row.get("Statut EDD", "") or "").strip()
    if edd and edd not in {"Validée", "Non requise", "Aucun"}:
        labels.append(f"EDD {edd}")
    return labels



def build_generic_review_prompt(vigilance: str) -> str:
    review_type = review_type_for_vigilance(vigilance)
    objective_1, objective_2 = review_objectives_for_vigilance(vigilance)
    return (
        f"Tu es un analyste conformité. Prépare les consignes de revue pour un dossier classé '{vigilance}'.\n"
        f"Type de revue : {review_type}.\n"
        f"Objectifs : 1) {objective_1} 2) {objective_2}\n\n"
        "Pour le SIREN {SIREN}, analyse l’ensemble des données transmises : toutes les données de base source, "
        "tous les indicateurs source, ainsi que le contexte de simulation (vigilance, risque, EDD, alertes actives, dates de revue).\n"
        "Rédige ensuite des consignes opérationnelles de revue. La réponse doit contenir : diagnostic bref, actions prioritaires, "
        "justificatifs à demander, points de contrôle, et statut de vigilance estimé après remédiation."
    )



def build_row_review_prompt(row: pd.Series) -> str:
    vigilance = str(row.get("Vigilance", "") or "").strip()
    review_type = review_type_for_vigilance(vigilance)
    objective_1, objective_2 = review_objectives_for_vigilance(vigilance)
    alerts = build_row_alert_labels(row)
    alert_text = ", ".join(alerts) if alerts else "Aucune alerte calculée active"
    next_review = format_short_date(row.get("Date prochaine revue")) or "Non renseignée"
    return (
        f"Tu es un analyste conformité. Prépare les consignes de revue du dossier SIREN {row.get('SIREN', '')}.\n"
        f"Type de revue : {review_type}. Régime de vigilance : {vigilance}.\n"
        f"Objectifs : 1) {objective_1} 2) {objective_2}\n"
        f"Contexte dossier : Dénomination = {row.get('Dénomination', 'Non renseigné')}, Risque = {row.get('Risque', 'Non renseigné')}, "
        f"EDD = {row.get('Statut EDD', 'Non renseigné')}, Date prochaine revue = {next_review}.\n"
        f"Alertes calculées actives : {alert_text}.\n"
        "Rédige des consignes de revue courtes, concrètes et priorisées. La sortie doit inclure : diagnostic, "
        "actions de remédiation, justificatifs à obtenir, points de contrôle, et statut de vigilance estimé après remédiation."
    )



def normalize_text_for_matching(value: object) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip()


def canonical_vigilance_label(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    raw_value = str(value).strip()
    if raw_value in VIGILANCE_ORDER:
        return raw_value
    normalized = normalize_text_for_matching(raw_value)
    for label in VIGILANCE_ORDER:
        if normalize_text_for_matching(label) == normalized:
            return label
    return ""


def canonical_risk_label(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    raw_value = str(value).strip()
    if raw_value in RISK_ORDER:
        return raw_value
    normalized = normalize_text_for_matching(raw_value)
    aliases = {
        "sans risque": "Aucun risque détecté",
        "aucun risque": "Aucun risque détecté",
        "aucun risque detecte": "Aucun risque détecté",
    }
    if normalized in aliases:
        return aliases[normalized]
    for label in RISK_ORDER:
        if normalize_text_for_matching(label) == normalized:
            return label
    return ""




def analysis_status_ui_label(value: object) -> str:
    status = canonical_risk_label(value) or ("" if value is None or pd.isna(value) else str(value).strip())
    return ANALYSIS_STATUS_DISPLAY.get(status, status)


def analysis_status_short_label(value: object) -> str:
    status = canonical_risk_label(value) or ("" if value is None or pd.isna(value) else str(value).strip())
    return ANALYSIS_STATUS_SHORT_LABELS.get(status, status)


def analysis_indicator_matches_keyword(normalized_text: str, keyword: str) -> bool:
    keyword_norm = normalize_text_for_matching(keyword)
    if not keyword_norm:
        return False
    if re.fullmatch(r"[a-z0-9]{1,4}", keyword_norm):
        tokens = [token for token in re.split(r"[^a-z0-9]+", normalized_text) if token]
        return keyword_norm in tokens
    return keyword_norm in normalized_text


def classify_analysis_indicator_family(indicator_name: object) -> str:
    normalized = normalize_text_for_matching(indicator_name)
    if not normalized:
        return "Segment / Client"

    for family, exact_values in ANALYSIS_INDICATOR_FAMILY_EXACT.items():
        normalized_exact = {normalize_text_for_matching(item) for item in exact_values}
        if normalized in normalized_exact:
            return family

    for family, keywords in ANALYSIS_INDICATOR_FAMILY_KEYWORDS.items():
        if any(analysis_indicator_matches_keyword(normalized, keyword) for keyword in keywords):
            return family

    return "Segment / Client"


def analysis_freshness_bucket(value: object) -> str:
    date_value = pd.to_datetime(value, errors="coerce")
    if pd.isna(date_value):
        return "Sans date"
    today = pd.Timestamp.utcnow().tz_localize(None).normalize()
    age_days = max(int((today - date_value.normalize()).days), 0)
    if age_days < 30:
        return "< 30 jours"
    if age_days <= 90:
        return "30 à 90 jours"
    return "> 90 jours"
def gemini_review_response_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "explication_generale": {
                "type": "string",
                "description": "Analyse générale du risque sur le SIREN, en 2 lignes maximum.",
            },
            "analyses_indicateurs": {
                "type": "array",
                "description": "Une entrée par indicateur réel de la source 02 analysé.",
                "items": {
                    "type": "object",
                    "properties": {
                        "nom_indicateur": {"type": "string"},
                        "constat": {"type": "string"},
                        "niveau_attention": {"type": "string"},
                        "mesures_attenuation": {"type": "string"},
                        "controles_necessaires": {"type": "string"},
                        "pieces_a_demander": {"type": "string"},
                    },
                    "required": [
                        "nom_indicateur",
                        "constat",
                        "niveau_attention",
                        "mesures_attenuation",
                        "controles_necessaires",
                        "pieces_a_demander",
                    ],
                },
            },
            "conclusion_generale": {
                "type": "string",
                "description": "Conclusion générale et justification du statut estimé.",
            },
            "statut_estime": {
                "type": "string",
                "enum": list(VIGILANCE_ORDER),
                "description": "Statut de vigilance estimé après remédiation.",
            },
        },
        "required": ["explication_generale", "analyses_indicateurs", "conclusion_generale", "statut_estime"],
    }


def canonical_indicator_name(value: object, available_names: list[str]) -> str:
    raw_value = str(value or "").strip()
    if not raw_value:
        return ""
    normalized = normalize_text_for_matching(raw_value)
    exact_map = {normalize_text_for_matching(name): name for name in available_names if str(name or "").strip()}
    if normalized in exact_map:
        return exact_map[normalized]
    for name in available_names:
        candidate = normalize_text_for_matching(name)
        if normalized in candidate or candidate in normalized:
            return name
    return raw_value


def normalize_gemini_indicator_analyses(raw_items: object, available_names: list[str]) -> list[dict[str, str]]:
    if not isinstance(raw_items, list):
        return []
    normalized_items: list[dict[str, str]] = []
    seen_names: set[str] = set()
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        name = canonical_indicator_name(item.get("nom_indicateur", item.get("nomIndicateur", "")), available_names)
        if not name:
            continue
        payload = {
            "nom_indicateur": name,
            "constat": str(item.get("constat", "") or "").strip(),
            "niveau_attention": str(item.get("niveau_attention", item.get("niveauAttention", "")) or "").strip(),
            "mesures_attenuation": str(item.get("mesures_attenuation", item.get("mesuresAttenuation", "")) or "").strip(),
            "controles_necessaires": str(item.get("controles_necessaires", item.get("controlesNecessaires", "")) or "").strip(),
            "pieces_a_demander": str(item.get("pieces_a_demander", item.get("piecesADemander", "")) or "").strip(),
        }
        if name in seen_names:
            continue
        seen_names.add(name)
        normalized_items.append(payload)
    order_map = {name: idx for idx, name in enumerate(available_names)}
    normalized_items.sort(key=lambda item: (order_map.get(item["nom_indicateur"], 10**6), normalize_text_for_matching(item["nom_indicateur"])))
    return normalized_items


def structured_explain_text_from_payload(explication_generale: str, analyses_indicateurs: list[dict[str, str]], conclusion_generale: str, statut_estime: str) -> str:
    parts: list[str] = []
    general = str(explication_generale or "").strip()
    if general:
        parts.append("PARTIE 1 — Analyse globale du risque\n" + general)
    indicator_blocks: list[str] = []
    for item in analyses_indicateurs:
        name = str(item.get("nom_indicateur", "") or "").strip()
        if not name:
            continue
        block_lines = [name]
        for label, key in [
            ("Constat", "constat"),
            ("Niveau d’attention", "niveau_attention"),
            ("Mesures d’atténuation", "mesures_attenuation"),
            ("Contrôles nécessaires", "controles_necessaires"),
            ("Pièces à demander", "pieces_a_demander"),
        ]:
            value = str(item.get(key, "") or "").strip()
            if value:
                block_lines.append(f"{label} : {value}")
        indicator_blocks.append("\n".join(block_lines))
    if indicator_blocks:
        parts.append("PARTIE 2 — Analyse détaillée indicateur par indicateur\n" + "\n\n".join(indicator_blocks))
    conclusion_lines: list[str] = []
    conclusion = str(conclusion_generale or "").strip()
    if conclusion:
        conclusion_lines.append(conclusion)
    if str(statut_estime or "").strip():
        conclusion_lines.append(f"Statut estimé proposé : {statut_estime}")
    if conclusion_lines:
        parts.append("PARTIE 3 — Conclusion et statut de vigilance estimé\n" + "\n".join(conclusion_lines))
    return "\n\n".join(parts).strip()


def review_simulation_parse_structured_ai_payload(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    try:
        parsed = json.loads(str(value or "").strip())
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def format_review_prompt_template(prompt_template: str, row: pd.Series) -> str:
    prompt = str(prompt_template or "").strip()
    if not prompt:
        return ""
    alert_text = ", ".join(build_row_alert_labels(row)) or "Aucune alerte calculée active"
    replacements = {
        "{SIREN}": str(row.get("SIREN", "") or "").strip(),
        "{DENOMINATION}": str(row.get("Dénomination", "") or "").strip(),
        "{VIGILANCE}": str(row.get("Vigilance", row.get(REVIEW_SIM_REAL_LABEL, "")) or "").strip(),
        "{RISQUE}": str(row.get("Risque", "") or "").strip(),
        "{EDD}": str(row.get("Statut EDD", "") or "").strip(),
        "{DATE_PROCHAINE_REVUE}": format_short_date(row.get("Date prochaine revue")) or "Non renseignée",
        "{ALERTES}": alert_text,
    }
    for placeholder, replacement in replacements.items():
        prompt = prompt.replace(placeholder, replacement)
    return prompt


def build_beclm_methodology_prompt_lines() -> str:
    lines: list[str] = []
    for title, items in [
        ("Limites d’information", BECLM_METHODOLOGY_FRAME.get("limites_information", [])),
        ("Posture attendue", BECLM_METHODOLOGY_FRAME.get("posture_attendue", [])),
        ("Exemples impératifs", BECLM_METHODOLOGY_FRAME.get("exemples_imperatifs", [])),
    ]:
        cleaned = [str(item).strip() for item in items if str(item).strip()]
        if not cleaned:
            continue
        lines.append(f"- {title} :")
        lines.extend([f"  - {item}" for item in cleaned])
    return "\n".join(lines)

def build_active_indicator_reference_prompt_lines(row: pd.Series) -> str:
    active_names = available_indicator_names_from_row(row)
    reference = indicator_reference_map()
    lines: list[str] = []
    for indicator_name in active_names:
        item = reference.get(indicator_reference_key(indicator_name))
        if not item:
            continue
        rules = INDICATOR_REFERENCE_STRICT_RULES.get(item["nom_indicateur"], {})
        lines.append(f"- {item['nom_indicateur']} ({item['famille']}) : {item['sens_metier']}")
        must_include = [str(value).strip() for value in rules.get("must_include_any", []) if str(value).strip()]
        must_not_include = [str(value).strip() for value in rules.get("must_not_include", []) if str(value).strip()]
        if must_include:
            lines.append(f"  Points à refléter explicitement dans l’analyse : {', '.join(must_include)}.")
        if must_not_include:
            lines.append(f"  Formulations interdites ou trompeuses : {', '.join(must_not_include)}.")
        interpretation_limit = INDICATOR_REFERENCE_INTERPRETATION_LIMITS.get(item["nom_indicateur"], "Les valeurs détaillées, seuils et paramétrages internes BeCLM ne sont pas communiqués ; raisonner à partir de la nature de l’alerte et rester prudent.")
        if interpretation_limit:
            lines.append(f"  Limites d’interprétation : {interpretation_limit}")
        due_diligence = INDICATOR_REFERENCE_DUE_DILIGENCE_GUIDANCE.get(item["nom_indicateur"], "Appliquer les meilleures pratiques de due diligence adaptées à la nature de l’alerte, de façon proportionnée, traçable et défendable.")
        if due_diligence:
            lines.append(f"  Approche attendue de due diligence : {due_diligence}")
    return "\n".join(lines)


def review_simulation_analysis_plain_text(item: dict[str, object]) -> str:
    parts = []
    for field in [
        "constat",
        "niveau_attention",
        "mesures_attenuation",
        "controles_necessaires",
        "pieces_a_demander",
    ]:
        value = str(item.get(field, "") or "").strip()
        if value:
            parts.append(value)
    return normalize_text_for_matching(" ".join(parts))


def validate_gemini_indicator_analyses(analyses_indicateurs: list[dict[str, object]]) -> list[str]:
    issues: list[str] = []
    for item in analyses_indicateurs:
        indicator_name = str(item.get("nom_indicateur", "") or "").strip()
        if not indicator_name:
            continue
        rules = INDICATOR_REFERENCE_STRICT_RULES.get(indicator_name, {})
        if not rules:
            continue
        text_norm = review_simulation_analysis_plain_text(item)
        if not text_norm:
            issues.append(f"{indicator_name} : analyse vide ou trop pauvre pour être fiable.")
            continue
        must_include = [normalize_text_for_matching(value) for value in rules.get("must_include_any", []) if str(value).strip()]
        if must_include and not any(value in text_norm for value in must_include):
            issues.append(
                f"{indicator_name} : l’analyse ne reflète pas clairement le sens métier attendu ({', '.join(rules.get('must_include_any', [])[:3])})."
            )
        for forbidden in [str(value).strip() for value in rules.get("must_not_include", []) if str(value).strip()]:
            if normalize_text_for_matching(forbidden) in text_norm:
                issues.append(f"{indicator_name} : l’analyse contient une formulation à proscrire ({forbidden}).")
        if indicator_name == "Risque pays FR" and "pays a risque" in text_norm and all(token not in text_norm for token in ["referentiel", "parametrage", "classement interne"]):
            issues.append("Risque pays FR : l’analyse suggère un pays à risque sans rappeler le caractère référentiel ou interne du signal.")
        if indicator_name == "Cross border" and "pays a risque" in text_norm and all(token not in text_norm for token in ["transfrontal", "international", "plusieurs pays"]):
            issues.append("Cross border : l’analyse dérive vers un risque pays au lieu de qualifier l’intensité des flux transfrontaliers.")
    return issues[:12]


def build_gemini_review_prompt(base_prompt: str, row: pd.Series, correction_issues: list[str] | None = None) -> str:
    prompt_parts: list[str] = []
    generic_prompt = format_review_prompt_template(base_prompt, row)
    if generic_prompt:
        prompt_parts.append("Consignes générales à respecter :\n" + generic_prompt)
    prompt_parts.append("Contexte détaillé du dossier :\n" + build_row_review_prompt(row))
    prompt_parts.append(
        "Garde-fous globaux d’interprétation (impératifs et prioritaires sur toute interprétation libre) :\n- "
        + "\n- ".join(INDICATOR_REFERENCE_GLOBAL_GUARDRAILS)
    )
    methodology_lines = build_beclm_methodology_prompt_lines()
    if methodology_lines:
        prompt_parts.append(
            "Cadre méthodologique BeCLM à respecter strictement :\n"
            + methodology_lines
        )
    active_indicator_reference_lines = build_active_indicator_reference_prompt_lines(row)
    if active_indicator_reference_lines:
        prompt_parts.append(
            "Référentiel durci des indicateurs actifs à respecter strictement :\n"
            + active_indicator_reference_lines
        )
    if correction_issues:
        prompt_parts.append(
            "Corrections impératives après contrôle qualité interne de la première réponse :\n- "
            + "\n- ".join(str(issue).strip() for issue in correction_issues if str(issue).strip())
        )
    prompt_parts.append(
        "Données source complètes du SIREN (analyse exhaustivement toutes les colonnes des objets JSON ci-dessous avant de conclure) :\n"
        + json.dumps(build_gemini_source_payload(row), ensure_ascii=False, indent=2)
    )
    prompt_parts.append(
        "Réponds exclusivement avec un JSON valide conforme au schéma demandé.\n"
        f"La valeur de 'statut_estime' doit être exactement l’une des suivantes : {', '.join(VIGILANCE_ORDER)}.\n"
        "Tu dois analyser chaque indicateur de la source 02 à partir de son sens métier BeCLM et des données réellement présentes dans la fiche.\n"
        "Les valeurs détaillées des indicateurs, les seuils de déclenchement, les pondérations et les paramétrages internes BeCLM ne te sont pas communiqués : tu ne peux pas les supposer ni bâtir ton dispositif comme si tu les connaissais.\n"
        "Tu interviens comme un compliance officer senior : pour chaque alerte, applique les meilleures pratiques de due diligence adaptées au cas, de façon proportionnée, opérationnelle et défendable.\n"
        "Ne renomme aucun indicateur. N’invente ni pays, ni personnes, ni faits, ni documents absents de la fiche.\n"
        "Quand une donnée métier précise manque, écris à préciser ou non communiqué par BeCLM au lieu d’extrapoler.\n"
        "Exemple impératif : pour Risque pays UE, si le pays exact n’est pas explicitement fourni, ne cite aucun pays et reste sur une diligence géographique générique au sens UE.\n"
        "Exemple impératif : pour SIREN / Catégorie juridique, si la forme exacte ou la logique de classement BeCLM n’est pas fournie, n’invente pas la raison précise du déclenchement et propose les diligences standard sur la structure juridique à clarifier.\n"
        "Pour les indicateurs pays, distingue explicitement GAFI, UE, FR, Bale Institute et Cross border ; ils ne sont pas synonymes.\n"
        "Le diagnostic et le statut estimé doivent être déterminés à partir de l’ensemble des données de base source, de l’ensemble des indicateurs source et des alertes calculées, et pas uniquement à partir de leur synthèse."
    )
    return "\n\n".join(prompt_parts)


def extract_gemini_response_text(response_payload: dict[str, object]) -> str:
    candidates = response_payload.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("Réponse Gemini sans candidat exploitable.")
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content")
        if not isinstance(content, dict):
            continue
        parts = content.get("parts")
        if not isinstance(parts, list):
            continue
        for part in parts:
            if isinstance(part, dict):
                text = str(part.get("text", "") or "").strip()
                if text:
                    return text
    raise ValueError("Réponse Gemini vide ou non textuelle.")


def parse_gemini_http_error(exc: HTTPError) -> str:
    try:
        payload = json.loads(exc.read().decode("utf-8", errors="replace"))
        if isinstance(payload, dict):
            message = payload.get("error", {}).get("message")
            if message:
                return str(message)
    except Exception:
        pass
    return f"Erreur HTTP {exc.code} lors de l’appel Gemini."


def call_gemini_json(prompt: str, api_key: str, model: str = GEMINI_MODEL_DEFAULT) -> dict[str, object]:
    api_key = str(api_key or "").strip()
    if not api_key:
        raise ValueError("La clé API Gemini est obligatoire.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": str(prompt or "")}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseJsonSchema": gemini_review_response_schema(),
            "temperature": 0.2,
        },
    }
    request = Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=GEMINI_API_TIMEOUT_SECONDS) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(parse_gemini_http_error(exc)) from exc
    except URLError as exc:
        raise RuntimeError(f"Impossible de joindre Gemini : {exc.reason}.") from exc
    except Exception as exc:
        raise RuntimeError(f"Erreur lors de l’appel Gemini : {exc}") from exc

    if not isinstance(response_payload, dict):
        raise ValueError("Réponse Gemini invalide.")
    if response_payload.get("error"):
        message = response_payload.get("error", {}).get("message")
        raise RuntimeError(str(message or "Erreur Gemini inconnue."))

    response_text = extract_gemini_response_text(response_payload)
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise ValueError("Gemini n’a pas renvoyé un JSON valide.") from exc

    if not isinstance(result, dict):
        raise ValueError("Le JSON Gemini attendu doit être un objet.")
    return result


def run_gemini_review_simulation(row: pd.Series, api_key: str, base_prompt: str, model: str = GEMINI_MODEL_DEFAULT) -> tuple[str, str, str]:
    available_names = available_indicator_names_from_row(row)
    correction_issues: list[str] | None = None
    last_validation_issues: list[str] = []

    for attempt_idx in range(2):
        result = call_gemini_json(
            build_gemini_review_prompt(base_prompt, row, correction_issues=correction_issues),
            api_key=api_key,
            model=model,
        )
        explication_generale = str(result.get("explication_generale", result.get("explicationGenerale", "")) or "").strip()
        conclusion_generale = str(result.get("conclusion_generale", result.get("conclusionGenerale", "")) or "").strip()
        estimated_status = canonical_vigilance_label(result.get("statut_estime", result.get("statutEstime", "")))
        analyses_indicateurs = normalize_gemini_indicator_analyses(
            result.get("analyses_indicateurs", result.get("analysesIndicateurs", [])),
            available_names,
        )
        explanation = structured_explain_text_from_payload(explication_generale, analyses_indicateurs, conclusion_generale, estimated_status)
        if not explication_generale:
            raise ValueError("Gemini a renvoyé un champ 'explication_generale' vide.")
        if not conclusion_generale:
            raise ValueError("Gemini a renvoyé un champ 'conclusion_generale' vide.")
        if not estimated_status:
            raise ValueError("Gemini a renvoyé un statut estimé invalide.")
        if available_names and not analyses_indicateurs:
            raise ValueError("Gemini n’a renvoyé aucune analyse structurée par indicateur de la source 02.")

        validation_issues = validate_gemini_indicator_analyses(analyses_indicateurs)
        if validation_issues and attempt_idx == 0:
            correction_issues = validation_issues
            last_validation_issues = validation_issues
            continue
        if validation_issues:
            raise ValueError(
                "Gemini a renvoyé une analyse encore insuffisamment contrainte par le référentiel durci : "
                + " | ".join(validation_issues[:6])
            )

        structured_payload = {
            "schema_version": 3,
            "explication_generale": explication_generale,
            "analyses_indicateurs": analyses_indicateurs,
            "conclusion_generale": conclusion_generale,
            "statut_estime": estimated_status,
            "controle_referentiel_durci": {
                "tentatives": attempt_idx + 1,
                "issues_corrigees": last_validation_issues if attempt_idx == 1 else [],
            },
        }
        return explanation, estimated_status, json.dumps(structured_payload, ensure_ascii=False)

    raise ValueError("Gemini n’a pas pu produire une analyse conforme au référentiel durci.")


def review_simulation_source_row(row: pd.Series, source_df: pd.DataFrame) -> pd.Series:
    soc = normalize_societe_id(pd.Series([row.get(SOC_COL, "")])).iloc[0]
    siren = normalize_siren(pd.Series([row.get("SIREN", "")])).iloc[0]
    match = source_df[(source_df[SOC_COL] == soc) & (source_df["SIREN"] == siren)]
    if match.empty:
        return pd.Series({
            SOC_COL: soc,
            "SIREN": siren,
            "Dénomination": row.get("Dénomination", ""),
            "Vigilance": row.get(REVIEW_SIM_REAL_LABEL, row.get("Vigilance", "")),
            "Risque": row.get("Risque", ""),
            "Statut EDD": row.get("Statut EDD", ""),
            "Date prochaine revue": row.get("Date prochaine revue"),
            f"{GEMINI_BASE_SOURCE_PREFIX}Dénomination": row.get("Dénomination", ""),
            f"{GEMINI_BASE_SOURCE_PREFIX}Statut EDD": row.get("Statut EDD", ""),
            f"{GEMINI_BASE_SOURCE_PREFIX}Date prochaine revue": row.get("Date prochaine revue"),
            f"{GEMINI_INDICATORS_SOURCE_PREFIX}Vigilance statut": row.get(REVIEW_SIM_REAL_LABEL, row.get("Vigilance", "")),
            f"{GEMINI_INDICATORS_SOURCE_PREFIX}Vigilance Date de mise à jour": row.get("Vigilance Date de mise à jour"),
            f"{GEMINI_INDICATORS_SOURCE_PREFIX}Cash intensité Statut": row.get("Cash intensité Statut"),
        })
    return match.iloc[0]


def apply_gemini_review_simulation_batch(
    working_df: pd.DataFrame,
    selected_indices: list[int],
    source_df: pd.DataFrame,
    api_key: str,
    base_prompt: str,
    model: str = GEMINI_MODEL_DEFAULT,
) -> tuple[pd.DataFrame, int, list[str]]:
    result = working_df.copy()
    batch_idx = [int(i) for i in selected_indices[:GEMINI_MAX_BATCH_SIZE] if 0 <= int(i) < len(result)]
    if not batch_idx:
        return result, 0, []

    source = source_df.copy()
    source[SOC_COL] = normalize_societe_id(source[SOC_COL])
    source["SIREN"] = normalize_siren(source["SIREN"])

    processed = 0
    errors: list[str] = []
    for idx in batch_idx:
        row_label = result.index[idx]
        row = result.iloc[idx]
        try:
            source_row = review_simulation_source_row(row, source)
            explanation, estimated_status, structured_payload = run_gemini_review_simulation(source_row, api_key=api_key, base_prompt=base_prompt, model=model)
            result.at[row_label, "Explique moi"] = explanation
            result.at[row_label, REVIEW_SIM_EST_LABEL] = estimated_status
            result.at[row_label, REVIEW_SIM_AI_STRUCTURED_LABEL] = structured_payload
            result.at[row_label, REVIEW_SIM_TREND_LABEL] = build_review_trend(
                result.at[row_label, REVIEW_SIM_REAL_LABEL],
                result.at[row_label, REVIEW_SIM_EST_LABEL],
            )
            processed += 1
        except Exception as exc:
            siren = str(row.get("SIREN", "") or "").strip() or f"ligne {idx + 1}"
            errors.append(f"{siren} : {exc}")
    return result, processed, errors


def merge_review_row_with_source_data(row: pd.Series, source_df: pd.DataFrame | None = None) -> pd.Series:
    if source_df is None or source_df.empty:
        return row.copy()
    source_row = review_simulation_source_row(row, source_df)
    merged = source_row.copy()
    for col in row.index:
        current_value = merged.get(col)
        if col not in merged.index or prompt_json_value(current_value) is None:
            merged[col] = row.get(col)
    return merged


def ensure_review_simulation_pdf_fonts() -> tuple[str, str]:
    regular_font = "Helvetica"
    bold_font = "Helvetica-Bold"
    if not REPORTLAB_AVAILABLE or pdfmetrics is None or TTFont is None:
        return regular_font, bold_font
    try:
        if REVIEW_SIM_PDF_FONT_REGULAR not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(REVIEW_SIM_PDF_FONT_REGULAR, "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
        if REVIEW_SIM_PDF_FONT_BOLD not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(REVIEW_SIM_PDF_FONT_BOLD, "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
        if REVIEW_SIM_PDF_FONT_ITALIC not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(REVIEW_SIM_PDF_FONT_ITALIC, "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"))
        if REVIEW_SIM_PDF_FONT_BOLDITALIC not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(REVIEW_SIM_PDF_FONT_BOLDITALIC, "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"))
        try:
            pdfmetrics.registerFontFamily(
                REVIEW_SIM_PDF_FONT_REGULAR,
                normal=REVIEW_SIM_PDF_FONT_REGULAR,
                bold=REVIEW_SIM_PDF_FONT_BOLD,
                italic=REVIEW_SIM_PDF_FONT_ITALIC,
                boldItalic=REVIEW_SIM_PDF_FONT_BOLDITALIC,
            )
        except Exception:
            pass
        regular_font = REVIEW_SIM_PDF_FONT_REGULAR
        bold_font = REVIEW_SIM_PDF_FONT_BOLD
    except Exception:
        pass
    return regular_font, bold_font


def review_simulation_pdf_styles() -> dict[str, ParagraphStyle]:
    if not REPORTLAB_AVAILABLE or colors is None or getSampleStyleSheet is None or ParagraphStyle is None:
        raise ModuleNotFoundError(PDF_DEPENDENCY_ERROR_MESSAGE)
    regular_font, bold_font = ensure_review_simulation_pdf_fonts()
    base_styles = getSampleStyleSheet()
    primary_color = colors.HexColor(PRIMARY_COLOR)
    muted_color = colors.HexColor("#5B6B7F")
    return {
        "title": ParagraphStyle(
            "ReviewSimPdfTitle",
            parent=base_styles["Title"],
            fontName=bold_font,
            fontSize=18,
            leading=22,
            textColor=primary_color,
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "ReviewSimPdfSubtitle",
            parent=base_styles["Normal"],
            fontName=regular_font,
            fontSize=9.5,
            leading=12,
            textColor=muted_color,
            spaceAfter=12,
        ),
        "section": ParagraphStyle(
            "ReviewSimPdfSection",
            parent=base_styles["Heading2"],
            fontName=bold_font,
            fontSize=11.5,
            leading=14,
            textColor=primary_color,
            spaceBefore=4,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "ReviewSimPdfBody",
            parent=base_styles["BodyText"],
            fontName=regular_font,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#12263A"),
        ),
        "body_muted": ParagraphStyle(
            "ReviewSimPdfBodyMuted",
            parent=base_styles["BodyText"],
            fontName=regular_font,
            fontSize=9,
            leading=12,
            textColor=muted_color,
        ),
        "field_name": ParagraphStyle(
            "ReviewSimPdfFieldName",
            parent=base_styles["BodyText"],
            fontName=bold_font,
            fontSize=8.6,
            leading=11,
            textColor=primary_color,
        ),
        "field_value": ParagraphStyle(
            "ReviewSimPdfFieldValue",
            parent=base_styles["BodyText"],
            fontName=regular_font,
            fontSize=8.8,
            leading=11.5,
            textColor=colors.HexColor("#12263A"),
        ),
        "table_header": ParagraphStyle(
            "ReviewSimPdfTableHeader",
            parent=base_styles["BodyText"],
            fontName=bold_font,
            fontSize=8.4,
            leading=10.4,
            textColor=colors.white,
        ),
        "table_header_small": ParagraphStyle(
            "ReviewSimPdfTableHeaderSmall",
            parent=base_styles["BodyText"],
            fontName=bold_font,
            fontSize=7.2,
            leading=8.8,
            textColor=colors.white,
        ),
        "body_small": ParagraphStyle(
            "ReviewSimPdfBodySmall",
            parent=base_styles["BodyText"],
            fontName=regular_font,
            fontSize=7.4,
            leading=9.2,
            textColor=colors.HexColor("#12263A"),
        ),
        "body_small_center": ParagraphStyle(
            "ReviewSimPdfBodySmallCenter",
            parent=base_styles["BodyText"],
            fontName=regular_font,
            fontSize=7.4,
            leading=9.2,
            textColor=colors.HexColor("#12263A"),
            alignment=1,
        ),
        "body_small_bold": ParagraphStyle(
            "ReviewSimPdfBodySmallBold",
            parent=base_styles["BodyText"],
            fontName=bold_font,
            fontSize=7.5,
            leading=9.3,
            textColor=primary_color,
        ),
    }


def review_simulation_pdf_value(field_name: str, value: object) -> str:
    normalized = prompt_json_value(value)
    if normalized is None:
        return "Non renseigné"
    if isinstance(normalized, bool):
        return "Oui" if normalized else "Non"
    if isinstance(normalized, float):
        label = str(field_name or "").lower()
        if 0 <= normalized <= 1 and any(token in label for token in ["part", "taux", "ratio", "cash intensité", "cross border", "%"]):
            return f"{normalized:.1%}"
        text_value = f"{normalized:,.4f}".replace(",", " ")
        text_value = text_value.rstrip("0").rstrip(".")
        return text_value or "0"
    if isinstance(normalized, (list, tuple, set)):
        items = [review_simulation_pdf_value(field_name, item) for item in normalized]
        items = [item for item in items if item and item != "Non renseigné"]
        return ", ".join(items) if items else "Aucune"
    if isinstance(normalized, dict):
        if not normalized:
            return "Aucune donnée"
        return json.dumps(normalized, ensure_ascii=False, indent=2)
    text_value = str(normalized).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text_value):
        dt = pd.to_datetime(text_value, errors="coerce")
        if not pd.isna(dt):
            return pd.Timestamp(dt).strftime("%d/%m/%Y")
    return text_value or "Non renseigné"


def review_simulation_pdf_paragraph(text: object, style: ParagraphStyle) -> Paragraph:
    rendered = str(text or "").strip() or "Non renseigné"
    return Paragraph(escape(rendered).replace("\n", "<br/>"), style)


def review_simulation_pdf_text_chunks(text: object, max_chars: int = 900) -> list[str]:
    rendered = str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not rendered:
        return ["Non renseigné"]

    raw_blocks = [block.strip() for block in re.split(r"\n\s*\n", rendered) if block.strip()]
    if not raw_blocks:
        raw_blocks = [rendered]

    logical_blocks: list[str] = []
    for block in raw_blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) > 1:
            logical_blocks.extend(lines)
        else:
            logical_blocks.append(block)

    chunks: list[str] = []
    for block in logical_blocks:
        normalized = re.sub(r"\s+", " ", block).strip()
        if not normalized:
            continue
        if len(normalized) <= max_chars:
            chunks.append(normalized)
            continue

        sentences = [part.strip() for part in re.split(r"(?<=[\.!?;:])\s+", normalized) if part.strip()]
        if not sentences:
            sentences = [normalized]

        current = ""
        for sentence in sentences:
            candidate = f"{current} {sentence}".strip()
            if current and len(candidate) > max_chars:
                chunks.append(current)
                current = sentence
            elif len(sentence) > max_chars:
                if current:
                    chunks.append(current)
                    current = ""
                for start_idx in range(0, len(sentence), max_chars):
                    piece = sentence[start_idx:start_idx + max_chars].strip()
                    if piece:
                        chunks.append(piece)
            else:
                current = candidate
        if current:
            chunks.append(current)

    return chunks or ["Non renseigné"]


def review_simulation_pdf_explanation_table(text: object, styles: dict[str, ParagraphStyle]) -> Table:
    rows = [[review_simulation_pdf_paragraph(chunk, styles["body"])] for chunk in review_simulation_pdf_text_chunks(text)]
    table = Table(rows, colWidths=[174 * mm], hAlign="LEFT", splitByRow=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F8FE")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#C6D8EA")),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -2), 0.35, colors.HexColor("#D9E6F2")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def review_simulation_pdf_explain_sections(text: object) -> dict[str, str]:
    rendered = str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not rendered:
        return {"1": "", "2": "", "3": ""}

    matches = list(re.finditer(r"(?i)\bPARTIE\s*([123])\b", rendered))
    if not matches:
        return {"1": rendered, "2": "", "3": ""}

    sections = {"1": "", "2": "", "3": ""}
    for idx, match in enumerate(matches):
        part_no = str(match.group(1))
        start_idx = match.start()
        end_idx = matches[idx + 1].start() if idx + 1 < len(matches) else len(rendered)
        chunk = rendered[start_idx:end_idx].strip()
        if chunk:
            sections[part_no] = chunk
    return sections


def review_simulation_pdf_summary_explanation_text(
    text: object,
    structured_payload: dict[str, object] | None = None,
) -> str:
    structured_payload = structured_payload or {}
    explication_generale = str(structured_payload.get("explication_generale", "") or "").strip()
    conclusion_generale = str(structured_payload.get("conclusion_generale", "") or "").strip()
    statut_estime = str(structured_payload.get("statut_estime", "") or "").strip()

    structured_parts: list[str] = []
    if explication_generale:
        structured_parts.append("PARTIE 1 — Analyse globale du risque\n" + explication_generale)
    conclusion_lines: list[str] = []
    if conclusion_generale:
        conclusion_lines.append(conclusion_generale)
    if statut_estime:
        conclusion_lines.append(f"Statut estimé proposé : {statut_estime}")
    if conclusion_lines:
        structured_parts.append("PARTIE 3 — Conclusion et statut de vigilance estimé\n" + "\n".join(conclusion_lines))
    if structured_parts:
        return "\n\n".join(structured_parts)

    sections = review_simulation_pdf_explain_sections(text)
    kept_parts = [sections.get("1", "").strip(), sections.get("3", "").strip()]
    kept_parts = [part for part in kept_parts if part]
    if kept_parts:
        return "\n\n".join(kept_parts)
    return str(text or "").strip() or "Non renseigné"


def review_simulation_pdf_strip_indicator_heading(chunk: str, indicator_name: str) -> str:
    rendered = str(chunk or "").strip()
    if not rendered:
        return ""
    escaped_name = re.escape(str(indicator_name or "").strip())
    if not escaped_name:
        return rendered
    pattern = re.compile(
        rf"^\s*(?:[-•]\s*|\d+[\.\)]\s*)?(?:indicateur\s*[:\-–—]\s*)?{escaped_name}\s*(?:[:\-–—]\s*)?",
        re.IGNORECASE,
    )
    cleaned = pattern.sub("", rendered, count=1).strip()
    return cleaned or rendered


def review_simulation_pdf_indicator_analysis_map(text: object, indicator_names: list[str]) -> dict[str, str]:
    sections = review_simulation_pdf_explain_sections(text)
    detail_text = sections.get("2", "").strip() or str(text or "").strip()
    indicator_names = [str(name or "").strip() for name in indicator_names if str(name or "").strip()]
    if not detail_text or not indicator_names:
        return {name: "" for name in indicator_names}

    analysis_map: dict[str, str] = {name: "" for name in indicator_names}
    heading_matches: list[tuple[int, str]] = []
    for name in indicator_names:
        escaped_name = re.escape(name)
        heading_pattern = re.compile(
            rf"(?im)(?:^|\n)\s*(?:[-•]\s*|\d+[\.\)]\s*)?(?:indicateur\s*[:\-–—]\s*)?{escaped_name}(?=\s*(?:[:\-–—]|\n|$))"
        )
        match = heading_pattern.search(detail_text)
        if match:
            heading_matches.append((match.start(), name))

    seen_names: set[str] = set()
    ordered_matches: list[tuple[int, str]] = []
    for start_idx, name in sorted(heading_matches, key=lambda item: (item[0], -len(item[1]))):
        if name in seen_names:
            continue
        seen_names.add(name)
        ordered_matches.append((start_idx, name))

    if ordered_matches:
        for idx, (start_idx, name) in enumerate(ordered_matches):
            end_idx = ordered_matches[idx + 1][0] if idx + 1 < len(ordered_matches) else len(detail_text)
            chunk = detail_text[start_idx:end_idx].strip()
            analysis_map[name] = review_simulation_pdf_strip_indicator_heading(chunk, name)

    if any(value.strip() for value in analysis_map.values()):
        return analysis_map

    raw_blocks = [block.strip() for block in re.split(r"\n\s*\n", detail_text) if block.strip()]
    if not raw_blocks:
        raw_blocks = [detail_text]
    for block in raw_blocks:
        matched_names = [name for name in indicator_names if re.search(re.escape(name), block, flags=re.IGNORECASE)]
        if len(matched_names) == 1:
            name = matched_names[0]
            cleaned = review_simulation_pdf_strip_indicator_heading(block, name)
            analysis_map[name] = f"{analysis_map[name]}\n\n{cleaned}".strip() if analysis_map[name].strip() else cleaned
    return analysis_map


def review_simulation_pdf_field_label(field_name: object) -> str:
    label = str(field_name or "").strip()
    return {
        "societe_id": "Société (id)",
    }.get(label, label)


def review_simulation_pdf_field_rows(data: dict[str, object], styles: dict[str, ParagraphStyle]) -> list[list[Paragraph]]:
    rows = [[review_simulation_pdf_paragraph("Champ", styles["table_header"]), review_simulation_pdf_paragraph("Valeur", styles["table_header"])]]
    for field_name, raw_value in data.items():
        rows.append([
            review_simulation_pdf_paragraph(review_simulation_pdf_field_label(field_name), styles["field_name"]),
            review_simulation_pdf_paragraph(review_simulation_pdf_value(field_name, raw_value), styles["field_value"]),
        ])
    return rows


def review_simulation_pdf_table(data: dict[str, object], styles: dict[str, ParagraphStyle], col_widths: list[float] | None = None) -> Table:
    col_widths = col_widths or [58 * mm, 116 * mm]
    rows = review_simulation_pdf_field_rows(data, styles)
    table = Table(rows, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PRIMARY_COLOR)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFE")]),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D6E1EE")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def review_simulation_pdf_indicator_table(
    data: dict[str, object],
    styles: dict[str, ParagraphStyle],
    col_widths: list[float] | None = None,
) -> Table:
    col_widths = col_widths or [58 * mm, 116 * mm]
    rows: list[list[Paragraph]] = [
        [
            review_simulation_pdf_paragraph("Champ", styles["table_header"]),
            review_simulation_pdf_paragraph("Valeur", styles["table_header"]),
        ]
    ]

    for field_name, raw_value in data.items():
        rows.append([
            review_simulation_pdf_paragraph(review_simulation_pdf_field_label(field_name), styles["field_name"]),
            review_simulation_pdf_paragraph(review_simulation_pdf_value(field_name, raw_value), styles["field_value"]),
        ])

    table = Table(rows, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PRIMARY_COLOR)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFE")]),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D6E1EE")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def review_simulation_pdf_indicator_analysis_box(
    indicator_name: str,
    analysis_text: object,
    styles: dict[str, ParagraphStyle],
) -> Table:
    chunks = review_simulation_pdf_text_chunks(analysis_text, max_chars=850)
    rows: list[list[Paragraph]] = [[review_simulation_pdf_paragraph(indicator_name, styles["table_header"])]]
    rows.extend([[review_simulation_pdf_paragraph(chunk, styles["body"])] for chunk in chunks])
    table = Table(rows, colWidths=[174 * mm], hAlign="LEFT", splitByRow=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PRIMARY_COLOR)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F7FAFE")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D6E1EE")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor(PRIMARY_COLOR)),
        ("LINEBELOW", (0, 1), (-1, -2), 0.35, colors.HexColor("#D9E6F2")),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def review_simulation_pdf_indicator_analysis_text(item: dict[str, object]) -> str:
    lines: list[str] = []
    for label, key in [
        ("Constat", "constat"),
        ("Niveau d’attention", "niveau_attention"),
        ("Mesures d’atténuation", "mesures_attenuation"),
        ("Contrôles nécessaires", "controles_necessaires"),
        ("Pièces à demander", "pieces_a_demander"),
    ]:
        value = str(item.get(key, "") or "").strip()
        if value:
            lines.append(f"{label} : {value}")
    return "\n\n".join(lines).strip()


def review_simulation_pdf_indicator_analysis_boxes(
    indicators_payload: dict[str, object],
    explain_text: object,
    styles: dict[str, ParagraphStyle],
    structured_payload: dict[str, object] | None = None,
) -> list[Table]:
    structured_payload = structured_payload or {}
    indicator_groups = indicator_group_map(list(indicators_payload.keys())) if indicators_payload else {}
    indicator_names = list(indicator_groups.keys())
    boxes: list[Table] = []

    structured_items = structured_payload.get("analyses_indicateurs")
    if isinstance(structured_items, list) and structured_items:
        structured_map: dict[str, dict[str, object]] = {}
        for raw_item in structured_items:
            if not isinstance(raw_item, dict):
                continue
            name = str(raw_item.get("nom_indicateur", "") or "").strip()
            if not name:
                continue
            structured_map[name] = raw_item
        ordered_names = [name for name in indicator_names if name in structured_map]
        for indicator_name in ordered_names:
            analysis_text = review_simulation_pdf_indicator_analysis_text(structured_map[indicator_name])
            if not analysis_text:
                continue
            boxes.append(review_simulation_pdf_indicator_analysis_box(indicator_name, analysis_text, styles))
        return boxes

    analysis_map = review_simulation_pdf_indicator_analysis_map(explain_text or "", indicator_names)
    for indicator_name in indicator_names:
        analysis_text = str(analysis_map.get(indicator_name, "") or "").strip()
        if not analysis_text:
            continue
        boxes.append(review_simulation_pdf_indicator_analysis_box(indicator_name, analysis_text, styles))
    return boxes



def review_simulation_pdf_rich_paragraph(html_text: object, style: ParagraphStyle) -> Paragraph:
    rendered = str(html_text or "").strip() or escape("Non renseigné")
    return Paragraph(rendered.replace("\n", "<br/>") , style)


def review_simulation_pdf_nullable_paragraph(text: object, style: ParagraphStyle) -> Paragraph:
    rendered = str(text or "").strip()
    if not rendered:
        return Paragraph("&nbsp;", style)
    return Paragraph(escape(rendered).replace("\n", "<br/>"), style)


def review_simulation_classification_status_colors(status: object) -> tuple[str, str]:
    try:
        return status_palette(status, "risk")
    except Exception:
        return ("#EEF2F7", "#334155")


def review_simulation_classification_vigilance_colors(vigilance: object) -> tuple[str, str]:
    value = str(vigilance or "").strip()
    if value == "NA":
        return ("#EEF2F7", "#334155")
    try:
        return status_palette(vigilance, "vigilance")
    except Exception:
        return ("#EEF2F7", "#334155")


def review_simulation_classification_vigilance_value(status: object, default_vigilance: object) -> str:
    normalized = canonical_risk_label(status) or str(status or "").strip()
    if normalized in {"Aucun risque détecté", "Non calculable"}:
        return "NA"
    rendered = canonical_vigilance_label(default_vigilance) or str(default_vigilance or "").strip()
    return rendered or "Non renseigné"


def review_simulation_classification_axis(indicator_name: object) -> str:
    family = classify_analysis_indicator_family(indicator_name)
    return CLASSIFICATION_AXIS_LABELS.get(family, "Client")


def review_simulation_classification_cotation(status: object) -> str:
    normalized = canonical_risk_label(status) or str(status or "").strip()
    return CLASSIFICATION_STATUS_COTATION.get(normalized, "")


def review_simulation_classification_new_cotation(status: object) -> str:
    normalized = canonical_risk_label(status) or str(status or "").strip()
    return CLASSIFICATION_STATUS_NEW_COTATION.get(normalized, "")


def review_simulation_classification_real_risk(status: object) -> str:
    normalized = canonical_risk_label(status) or str(status or "").strip()
    return CLASSIFICATION_STATUS_REAL_RISK.get(normalized, "")


def review_simulation_classification_comment_html(comment: object) -> str:
    value = prompt_json_value(comment)
    text_value = "" if value is None else str(value).strip()
    if not text_value or normalize_text_for_matching(text_value) in {"non renseigne", "none", "nan"}:
        return f"<i>{escape(CLASSIFICATION_COMMENT_PLACEHOLDER_TEXT)}</i>"
    return escape(text_value).replace("\n", "<br/>")


def review_simulation_classification_beclm_percent(value: object) -> str:
    normalized = prompt_json_value(value)
    if normalized is None:
        return "Non renseigné"
    try:
        numeric = float(normalized)
    except Exception:
        text_value = str(normalized).strip()
        return text_value or "Non renseigné"
    if 0 <= numeric <= 1:
        numeric *= 100
    return f"{numeric:.2f} %".replace(".", ",")


def review_simulation_classification_date_text(value: object) -> str:
    text_value = format_short_date(value)
    if text_value:
        return text_value
    rendered = review_simulation_pdf_value("Date de mise à jour", value)
    return rendered if rendered != "Non renseigné" else "Non renseignée"


def review_simulation_classification_structured_indicator_map(
    structured_payload: dict[str, object] | None,
    available_names: list[str],
) -> dict[str, dict[str, str]]:
    structured_payload = structured_payload or {}
    items = normalize_gemini_indicator_analyses(structured_payload.get("analyses_indicateurs"), available_names)
    return {str(item.get("nom_indicateur", "") or "").strip(): item for item in items if str(item.get("nom_indicateur", "") or "").strip()}


def review_simulation_classification_scenario_html(indicator_name: str, data: dict[str, object]) -> str:
    status = canonical_risk_label(data.get("Statut")) or review_simulation_pdf_value("Statut", data.get("Statut"))
    date_text = review_simulation_classification_date_text(data.get("Date de mise à jour"))
    return "<br/>".join([
        f"<b>{escape(indicator_name)}</b>",
        f"<b>% de risque BeCLM :</b> {escape(review_simulation_classification_beclm_percent(data.get('Valeur')))}",
        f"<b>Statut :</b> {escape(status or 'Non renseigné')}",
        f"<b>Date :</b> {escape(date_text)}",
        f"<b>Commentaire BeCLM :</b> {review_simulation_classification_comment_html(data.get('Commentaire'))}",
    ])


def review_simulation_classification_dispositif_html(
    status: object,
    comment: object,
    structured_item: dict[str, object] | None = None,
) -> str:
    normalized = canonical_risk_label(status) or str(status or "").strip()
    if normalized != "Risque potentiel":
        return review_simulation_classification_comment_html(comment)

    structured_item = structured_item or {}
    blocks: list[str] = []
    for label, key in [
        ("Mesures d’atténuation", "mesures_attenuation"),
        ("Contrôles nécessaires", "controles_necessaires"),
        ("Pièces à demander", "pieces_a_demander"),
    ]:
        value = str(structured_item.get(key, "") or "").strip()
        if value:
            blocks.append(f"<b>{escape(label)} :</b> {escape(value).replace(chr(10), '<br/>')}")
    if blocks:
        return "<br/><br/>".join(blocks)
    return f"<i>{escape(CLASSIFICATION_AI_PLACEHOLDER_TEXT)}</i>"


def review_simulation_classification_rows(
    row: pd.Series,
    source_row: pd.Series,
) -> dict[str, list[dict[str, object]]]:
    payload = build_gemini_source_payload(source_row)
    grouped_items = payload.get("indicateurs_source_groupes") if isinstance(payload.get("indicateurs_source_groupes"), list) else []
    available_names = [str(item.get("nom_indicateur", "") or "").strip() for item in grouped_items if str(item.get("nom_indicateur", "") or "").strip()]
    structured_payload = review_simulation_parse_structured_ai_payload(row.get(REVIEW_SIM_AI_STRUCTURED_LABEL, ""))
    structured_map = review_simulation_classification_structured_indicator_map(structured_payload, available_names)
    default_vigilance_value = canonical_vigilance_label(row.get(REVIEW_SIM_EST_LABEL, "")) or canonical_vigilance_label(structured_payload.get("statut_estime", "")) or str(row.get(REVIEW_SIM_EST_LABEL, "") or structured_payload.get("statut_estime", "") or "Non renseigné").strip() or "Non renseigné"

    by_axis: dict[str, list[dict[str, object]]] = {axis: [] for axis in CLASSIFICATION_AXIS_ORDER}
    for item in grouped_items:
        indicator_name = str(item.get("nom_indicateur", "") or "").strip()
        if not indicator_name or indicator_name in CLASSIFICATION_EXCLUDED_INDICATORS:
            continue
        data = item.get("donnees") if isinstance(item.get("donnees"), dict) else {}
        status = canonical_risk_label(data.get("Statut")) or str(data.get("Statut", "") or "").strip() or "Non renseigné"
        axis = review_simulation_classification_axis(indicator_name)
        by_axis.setdefault(axis, []).append({
            "indicator_name": indicator_name,
            "scenario_html": review_simulation_classification_scenario_html(indicator_name, data),
            "status": status,
            "cotation": review_simulation_classification_cotation(status),
            "dispositif_html": review_simulation_classification_dispositif_html(status, data.get("Commentaire"), structured_map.get(indicator_name)),
            "new_cotation": review_simulation_classification_new_cotation(status),
            "real_risk": review_simulation_classification_real_risk(status),
            "vigilance": review_simulation_classification_vigilance_value(status, default_vigilance_value),
        })

    def _sort_key(entry: dict[str, object]) -> tuple[int, str]:
        status_value = canonical_risk_label(entry.get("status")) or str(entry.get("status", "") or "")
        try:
            rank = RISK_ORDER.index(status_value)
        except ValueError:
            rank = len(RISK_ORDER)
        return rank, normalize_text_for_matching(entry.get("indicator_name", ""))

    for axis in list(by_axis.keys()):
        by_axis[axis] = sorted(by_axis[axis], key=_sort_key)
    return by_axis


def review_simulation_classification_logo_reader() -> object | None:
    if not LOGO_DATA_URI or ImageReader is None:
        return None
    if not str(LOGO_DATA_URI).startswith("data:image"):
        return None
    try:
        _meta, encoded = str(LOGO_DATA_URI).split(",", 1)
        return ImageReader(BytesIO(base64.b64decode(encoded)))
    except Exception:
        return None


def review_simulation_classification_legend_table(styles: dict[str, ParagraphStyle]) -> Table:
    statuses = [
        "Risque avéré",
        "Risque potentiel",
        "Risque mitigé",
        "Risque levé",
        "Aucun risque détecté",
        "Non calculable",
    ]
    header_row: list[Paragraph] = []
    value_row: list[Paragraph] = []
    for status in statuses:
        header_row.append(review_simulation_pdf_paragraph(status, styles["table_header_small"]))
        value_row.append(review_simulation_pdf_nullable_paragraph(review_simulation_classification_cotation(status), styles["body_small_center"]))
    table = Table([header_row, value_row], colWidths=[40 * mm] * len(statuses), hAlign="LEFT")
    style_commands: list[tuple[object, ...]] = [
        ("BOX", (0, 0), (-1, -1), 0.45, colors.HexColor("#D6E1EE")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D6E1EE")),
        ("BACKGROUND", (0, 1), (-1, 1), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    for col_idx, status in enumerate(statuses):
        bg, fg = review_simulation_classification_status_colors(status)
        style_commands.extend([
            ("BACKGROUND", (col_idx, 0), (col_idx, 0), colors.HexColor(bg)),
            ("TEXTCOLOR", (col_idx, 0), (col_idx, 0), colors.HexColor(fg)),
            ("TEXTCOLOR", (col_idx, 1), (col_idx, 1), colors.HexColor(bg if bg != '#EEF2F7' else '#334155')),
        ])
    table.setStyle(TableStyle(style_commands))
    return table


def review_simulation_classification_axis_table(
    axis_label: str,
    rows_data: list[dict[str, object]],
    styles: dict[str, ParagraphStyle],
) -> Table:
    headers = [
        "Sous-catégories et scénarios de risques",
        "Risque BeCLM",
        "Cot.",
        "Dispositif de maîtrise du risque",
        "Nouvelle cotation",
        "Risque réel",
        "Niveau de vigilance applicable",
    ]
    rows: list[list[Paragraph]] = [[review_simulation_pdf_paragraph(header, styles["table_header_small"]) for header in headers]]
    for item in rows_data:
        rows.append([
            review_simulation_pdf_rich_paragraph(item.get("scenario_html", ""), styles["body_small"]),
            review_simulation_pdf_paragraph(item.get("status", ""), styles["body_small_center"]),
            review_simulation_pdf_nullable_paragraph(item.get("cotation", ""), styles["body_small_center"]),
            review_simulation_pdf_rich_paragraph(item.get("dispositif_html", ""), styles["body_small"]),
            review_simulation_pdf_nullable_paragraph(item.get("new_cotation", ""), styles["body_small_center"]),
            review_simulation_pdf_nullable_paragraph(item.get("real_risk", ""), styles["body_small_center"]),
            review_simulation_pdf_paragraph(item.get("vigilance", ""), styles["body_small_center"]),
        ])
    table = Table(rows, colWidths=[72 * mm, 24 * mm, 12 * mm, 74 * mm, 18 * mm, 22 * mm, 23 * mm], repeatRows=1, hAlign="LEFT", splitByRow=1)
    style_commands: list[tuple[object, ...]] = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PRIMARY_COLOR)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D6E1EE")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFE")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ALIGN", (1, 0), (2, -1), "CENTER"),
        ("ALIGN", (4, 0), (6, -1), "CENTER"),
    ]
    for row_idx, item in enumerate(rows_data, start=1):
        status = item.get("status", "")
        risk_bg, risk_fg = review_simulation_classification_status_colors(status)
        vigilance_bg, vigilance_fg = review_simulation_classification_vigilance_colors(item.get("vigilance", ""))
        style_commands.extend([
            ("BACKGROUND", (1, row_idx), (1, row_idx), colors.HexColor(risk_bg)),
            ("TEXTCOLOR", (1, row_idx), (1, row_idx), colors.HexColor(risk_fg)),
            ("BACKGROUND", (5, row_idx), (5, row_idx), colors.HexColor(risk_bg)),
            ("TEXTCOLOR", (5, row_idx), (5, row_idx), colors.HexColor(risk_fg)),
            ("BACKGROUND", (6, row_idx), (6, row_idx), colors.HexColor(vigilance_bg)),
            ("TEXTCOLOR", (6, row_idx), (6, row_idx), colors.HexColor(vigilance_fg)),
        ])
        if str(item.get("cotation", "") or "").strip():
            style_commands.append(("TEXTCOLOR", (2, row_idx), (2, row_idx), colors.HexColor(risk_bg)))
        if str(item.get("new_cotation", "") or "").strip():
            style_commands.append(("TEXTCOLOR", (4, row_idx), (4, row_idx), colors.HexColor(risk_bg)))
    table.setStyle(TableStyle(style_commands))
    return table


def build_review_simulation_classification_pdf_story(
    row: pd.Series,
    source_row: pd.Series,
    generated_at_utc: datetime,
) -> tuple[list[object], dict[str, ParagraphStyle]]:
    styles = review_simulation_pdf_styles()
    generated_text = pd.Timestamp(generated_at_utc).strftime("%d/%m/%Y %H:%M UTC")
    classification_rows = review_simulation_classification_rows(row, source_row)
    estimated_vigilance = canonical_vigilance_label(row.get(REVIEW_SIM_EST_LABEL, "")) or str(row.get(REVIEW_SIM_EST_LABEL, "") or "Non renseigné").strip() or "Non renseigné"
    total_rows = sum(len(items) for items in classification_rows.values())

    metadata = {
        "Société": row.get(SOC_COL, ""),
        "SIREN": row.get("SIREN", ""),
        "Dénomination": row.get("Dénomination", ""),
        "Type de revue": row.get("Type de revue", review_type_for_vigilance(row.get(REVIEW_SIM_REAL_LABEL, row.get("Vigilance", "")))),
        "Statut estimé IA retenu": estimated_vigilance,
        "Indicateurs classés": total_rows,
        "Date de génération": generated_text,
    }
    methodology_text = (
        "Le document reprend la logique de la classification LCB-FT et regroupe les indicateurs BeCLM par axes Client, Pays, Produit et Canal.\n\n"
        "La colonne ‘Risque BeCLM’ reprend le statut source de l’indicateur. La ‘Cotation’, la ‘Nouvelle cotation’ et le ‘Risque réel’ sont dérivés directement de ce statut selon les règles métier validées.\n\n"
        "Le ‘Niveau de vigilance applicable’ reprend la valeur estimée par l’IA dans le premier PDF de Revue & Simulation, sauf pour les statuts Sans risque et Non calculable où la valeur affichée est ‘NA’."
    )

    story: list[object] = [
        review_simulation_pdf_paragraph(
            f"Classification - {review_simulation_pdf_value('SIREN', row.get('SIREN', ''))} - {review_simulation_pdf_value('Dénomination', row.get('Dénomination', ''))}",
            styles["title"],
        ),
        review_simulation_pdf_paragraph(
            f"Document de classification structurée généré le {generated_text}.",
            styles["subtitle"],
        ),
        review_simulation_pdf_table(metadata, styles, col_widths=[62 * mm, 171 * mm]),
        Spacer(1, 5 * mm),
        review_simulation_pdf_paragraph("Méthodologie de lecture", styles["section"]),
        review_simulation_pdf_explanation_table(methodology_text, styles),
        Spacer(1, 5 * mm),
        review_simulation_pdf_paragraph("Correspondance statut BeCLM / cotation", styles["section"]),
        review_simulation_classification_legend_table(styles),
        Spacer(1, 6 * mm),
    ]

    has_rows = False
    for axis_label in CLASSIFICATION_AXIS_ORDER:
        axis_rows = classification_rows.get(axis_label, [])
        if not axis_rows:
            continue
        if has_rows:
            story.append(PageBreak())
        has_rows = True
        story.extend([
            review_simulation_pdf_paragraph(axis_label, styles["section"]),
            review_simulation_classification_axis_table(axis_label, axis_rows, styles),
            Spacer(1, 5 * mm),
        ])

    if not has_rows:
        story.extend([
            review_simulation_pdf_paragraph("Classification par axe", styles["section"]),
            review_simulation_pdf_explanation_table("Aucun indicateur source exploitable n’est disponible pour construire le tableau de classification.", styles),
        ])
    return story, styles


def write_review_simulation_classification_pdf(
    row: pd.Series,
    source_df: pd.DataFrame | None = None,
) -> Path | None:
    if not REPORTLAB_AVAILABLE:
        raise ModuleNotFoundError(PDF_DEPENDENCY_ERROR_MESSAGE)
    explain_text = str(row.get("Explique moi", "") or "").strip()
    if not explain_text:
        return None

    source_row = merge_review_row_with_source_data(row, source_df=source_df)
    pdf_path = review_simulation_classification_pdf_path(row)
    generated_at_utc = datetime.now(timezone.utc)
    story, styles = build_review_simulation_classification_pdf_story(row, source_row, generated_at_utc)
    page_size = landscape(A4)
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=page_size,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=22 * mm,
        bottomMargin=14 * mm,
        title=f"Classification - {row.get('SIREN', '')}",
        author=PAGE_TITLE,
        subject="Classification structurée des risques BeCLM",
    )

    regular_font = styles["body"].fontName
    primary_color = colors.HexColor(PRIMARY_COLOR)
    muted_color = colors.HexColor("#5B6B7F")
    logo_reader = review_simulation_classification_logo_reader()

    def _draw_page(canvas, doc_obj):
        canvas.saveState()
        width, height = doc_obj.pagesize
        header_line_y = height - 15 * mm
        canvas.setStrokeColor(primary_color)
        canvas.setLineWidth(0.8)
        canvas.line(doc_obj.leftMargin, header_line_y, width - doc_obj.rightMargin, header_line_y)
        if logo_reader is not None:
            logo_size = 10 * mm
            logo_x = width - doc_obj.rightMargin - logo_size
            logo_y = height - 4 * mm - logo_size
            try:
                canvas.drawImage(logo_reader, logo_x, logo_y, width=logo_size, height=logo_size, preserveAspectRatio=True, mask='auto')
            except Exception:
                pass
        canvas.setFont(regular_font, 8)
        canvas.setFillColor(primary_color)
        canvas.drawString(doc_obj.leftMargin, 9 * mm, f"{PAGE_TITLE} - Classification BeCLM")
        canvas.setFillColor(muted_color)
        canvas.drawRightString(width - doc_obj.rightMargin, 9 * mm, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    return pdf_path


def review_simulation_summary_payload(row: pd.Series) -> dict[str, object]:
    return {
        "Société": row.get(SOC_COL, ""),
        "SIREN": row.get("SIREN", ""),
        "Dénomination": row.get("Dénomination", ""),
        "Type de revue": row.get("Type de revue", review_type_for_vigilance(row.get(REVIEW_SIM_REAL_LABEL, row.get("Vigilance", "")))),
        "Statut de vigilance réel": row.get(REVIEW_SIM_REAL_LABEL, row.get("Vigilance", "")),
        "Statut estimé après remédiation": row.get(REVIEW_SIM_EST_LABEL, ""),
        "Indicateur de tendance": row.get(REVIEW_SIM_TREND_LABEL, ""),
        "Risque": row.get("Risque", ""),
        "Statut EDD": row.get("Statut EDD", ""),
        "Date prochaine revue": row.get("Date prochaine revue", ""),
        "Alertes actives": row.get("Alertes actives", ", ".join(build_row_alert_labels(row)) or "Aucune"),
    }


def build_review_simulation_pdf_story(
    row: pd.Series,
    source_row: pd.Series,
    generated_at_utc: datetime,
    prompt_template: str = "",
) -> tuple[list[object], dict[str, ParagraphStyle]]:
    styles = review_simulation_pdf_styles()
    payload = build_gemini_source_payload(source_row)
    summary_payload = review_simulation_summary_payload(source_row)
    context_payload = payload.get("contexte_simulation") if isinstance(payload.get("contexte_simulation"), dict) else {}
    base_payload = payload.get("donnees_base_source") if isinstance(payload.get("donnees_base_source"), dict) else {}
    indicators_payload = payload.get("indicateurs_source") if isinstance(payload.get("indicateurs_source"), dict) else {}
    generated_text = pd.Timestamp(generated_at_utc).strftime("%d/%m/%Y %H:%M UTC")
    explain_text = str(row.get("Explique moi", "") or "").strip()
    structured_ai_payload = review_simulation_parse_structured_ai_payload(row.get(REVIEW_SIM_AI_STRUCTURED_LABEL, ""))
    explain_summary_text = review_simulation_pdf_summary_explanation_text(explain_text or "", structured_ai_payload)
    indicator_analysis_boxes = review_simulation_pdf_indicator_analysis_boxes(indicators_payload, explain_text or "", styles, structured_ai_payload)
    prompt_text = format_review_prompt_template(prompt_template, source_row)

    story: list[object] = [
        review_simulation_pdf_paragraph(
            f"Revue & Simulation - SIREN {review_simulation_pdf_value('SIREN', row.get('SIREN', ''))}",
            styles["title"],
        ),
        review_simulation_pdf_paragraph(
            f"Dossier : {review_simulation_pdf_value('Dénomination', row.get('Dénomination', ''))} - Généré le {generated_text}.",
            styles["subtitle"],
        ),
        review_simulation_pdf_paragraph("Synthèse du dossier", styles["section"]),
        review_simulation_pdf_table(summary_payload, styles, col_widths=[60 * mm, 114 * mm]),
        Spacer(1, 5 * mm),
        review_simulation_pdf_paragraph("Explication & Consignes générales", styles["section"]),
    ]

    explanation_box = review_simulation_pdf_explanation_table(explain_summary_text or "Non renseigné", styles)
    story.extend([
        explanation_box,
        Spacer(1, 5 * mm),
    ])

    if indicator_analysis_boxes:
        for idx, indicator_box in enumerate(indicator_analysis_boxes):
            story.append(indicator_box)
            if idx < len(indicator_analysis_boxes) - 1:
                story.append(Spacer(1, 4 * mm))
        story.append(Spacer(1, 5 * mm))

    story.extend([
        review_simulation_pdf_paragraph("Contexte de simulation", styles["section"]),
        review_simulation_pdf_table(context_payload or {"Contexte": "Aucune donnée complémentaire"}, styles),
        Spacer(1, 5 * mm),
        review_simulation_pdf_paragraph("Données de base source", styles["section"]),
        review_simulation_pdf_table(base_payload or {"Données de base source": "Aucune donnée disponible"}, styles),
        Spacer(1, 5 * mm),
        review_simulation_pdf_paragraph("Indicateurs source", styles["section"]),
        review_simulation_pdf_indicator_table(indicators_payload or {"Indicateurs source": "Aucune donnée disponible"}, styles),
    ])

    if prompt_text:
        story.extend([
            Spacer(1, 5 * mm),
            review_simulation_pdf_paragraph("Prompt Gemini utilisé", styles["section"]),
            review_simulation_pdf_table({"Consignes générales": prompt_text}, styles, col_widths=[58 * mm, 116 * mm]),
        ])

    return story, styles


def write_review_simulation_pdf(
    row: pd.Series,
    source_df: pd.DataFrame | None = None,
    prompt_template: str = "",
) -> Path | None:
    if not REPORTLAB_AVAILABLE:
        raise ModuleNotFoundError(PDF_DEPENDENCY_ERROR_MESSAGE)
    explain_text = str(row.get("Explique moi", "") or "").strip()
    if not explain_text:
        return None

    source_row = merge_review_row_with_source_data(row, source_df=source_df)
    pdf_path = review_simulation_pdf_path(row)
    generated_at_utc = datetime.now(timezone.utc)
    story, styles = build_review_simulation_pdf_story(row, source_row, generated_at_utc, prompt_template=prompt_template)

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=16 * mm,
        title=f"Revue & Simulation - {row.get('SIREN', '')}",
        author=PAGE_TITLE,
        subject="Synthèse de revue et simulation",
    )

    regular_font = styles["body"].fontName
    primary_color = colors.HexColor(PRIMARY_COLOR)
    muted_color = colors.HexColor("#5B6B7F")

    def _draw_page(canvas, doc_obj):
        canvas.saveState()
        canvas.setStrokeColor(primary_color)
        canvas.setLineWidth(0.8)
        canvas.line(doc_obj.leftMargin, A4[1] - 12 * mm, A4[0] - doc_obj.rightMargin, A4[1] - 12 * mm)
        canvas.setFont(regular_font, 8)
        canvas.setFillColor(muted_color)
        canvas.drawString(doc_obj.leftMargin, 10 * mm, f"{PAGE_TITLE} - Revues & Simulations")
        canvas.drawRightString(A4[0] - doc_obj.rightMargin, 10 * mm, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    return pdf_path


def delete_review_simulation_pdfs(row: pd.Series) -> None:
    for item in review_simulation_pdf_entries_for_row(row):
        path = item.get("path")
        if isinstance(path, Path) and path.exists():
            path.unlink()


def sync_review_simulation_pdfs(
    rows_df: pd.DataFrame,
    source_df: pd.DataFrame | None = None,
    prompt_template: str = "",
) -> tuple[int, list[str]]:
    if rows_df is None or rows_df.empty:
        return 0, []
    if not REPORTLAB_AVAILABLE:
        return 0, [PDF_DEPENDENCY_ERROR_MESSAGE]

    generated = 0
    errors: list[str] = []
    for _, row in rows_df.iterrows():
        siren = str(row.get("SIREN", "") or "").strip() or "SIREN inconnu"
        explain_text = str(row.get("Explique moi", "") or "").strip()
        if not explain_text:
            delete_review_simulation_pdfs(row)
            continue
        try:
            if write_review_simulation_pdf(row, source_df=source_df, prompt_template=prompt_template):
                generated += 1
        except Exception as exc:
            errors.append(f"PDF revue {siren} : {exc}")
        try:
            if write_review_simulation_classification_pdf(row, source_df=source_df):
                generated += 1
        except Exception as exc:
            errors.append(f"PDF classification {siren} : {exc}")
    return generated, errors


def review_simulation_available_pdfs(
    df: pd.DataFrame,
    selected_indices: list[int] | None = None,
) -> list[dict[str, object]]:
    if df is None or df.empty:
        return []

    if selected_indices:
        row_indices = [int(i) for i in selected_indices if 0 <= int(i) < len(df)]
    else:
        row_indices = list(range(len(df)))

    items: list[dict[str, object]] = []
    seen_paths: set[str] = set()
    for idx in row_indices:
        row = df.iloc[idx]
        for entry in review_simulation_pdf_entries_for_row(row):
            pdf_path = entry.get("path")
            if not isinstance(pdf_path, Path) or not pdf_path.exists():
                continue
            resolved_path = str(pdf_path.resolve())
            if resolved_path in seen_paths:
                continue
            seen_paths.add(resolved_path)
            items.append({
                "row": row,
                "kind": entry.get("kind", "pdf"),
                "path": pdf_path,
                "label": entry.get("label", f"{row.get('SIREN', '')} - {row.get('Dénomination', '')}"),
                "download_name": entry.get("download_name", pdf_path.name),
            })
    return items


def review_simulation_pdfs_zip_bytes(items: list[dict[str, object]]) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in items:
            path = item.get("path")
            download_name = str(item.get("download_name", "document.pdf") or "document.pdf")
            if isinstance(path, Path) and path.exists():
                archive.writestr(download_name, path.read_bytes())
    return buffer.getvalue()


def review_simulation_single_download_payload(items: list[dict[str, object]]) -> tuple[bytes | None, str, str]:
    if not items:
        return None, "revue_simulation.pdf", "application/pdf"
    if len(items) == 1:
        path = items[0].get("path")
        if isinstance(path, Path) and path.exists():
            return path.read_bytes(), str(items[0].get("download_name", path.name)), "application/pdf"
        return None, "revue_simulation.pdf", "application/pdf"

    first_row = items[0].get("row")
    if isinstance(first_row, pd.Series):
        siren = safe_filename_component(first_row.get("SIREN", ""), fallback="siren")
        denomination = safe_filename_component(first_row.get("Dénomination", ""), fallback="dossier")
        file_name = f"documents_pdf_{siren}_{denomination}.zip"
    else:
        file_name = "documents_pdf.zip"
    return review_simulation_pdfs_zip_bytes(items), file_name, "application/zip"


def build_simulated_review_explanation(row: pd.Series) -> str:
    vigilance = str(row.get("Vigilance", "") or "").strip()
    review_type = review_type_for_vigilance(vigilance)
    alerts = build_row_alert_labels(row)
    actions: list[str] = []
    if "Justificatifs incomplets" in alerts:
        actions.append("compléter et contrôler les justificatifs manquants")
    if "Sans prochaine revue" in alerts:
        actions.append("programmer immédiatement une prochaine revue")
    if "Revue trop ancienne" in alerts:
        actions.append("mettre à jour l’analyse et tracer la revue")
    if "Cross-border élevé" in alerts:
        actions.append("documenter la logique économique des flux transfrontières")
    if "Cash intensité élevée" in alerts:
        actions.append("vérifier la cohérence entre activité déclarée et flux cash")
    if "Risque avéré" in alerts:
        actions.append("escalader le dossier au valideur / conformité sans délai")
    elif "Risque potentiel" in alerts:
        actions.append("qualifier le risque potentiel et confirmer ou infirmer le signal")
    edd = str(row.get("Statut EDD", "") or "").strip()
    if edd and edd not in {"Validée", "Non requise", "Aucun"}:
        actions.append("finaliser le parcours de diligence renforcée et documenter la décision")
    if not actions:
        actions.append("confirmer la cohérence générale du dossier et maintenir le cycle de revue")
    actions_text = "; ".join(dict.fromkeys(actions))
    return (
        f"{review_type}. Actions suggérées : {actions_text}. "
        f"Le statut de vigilance espéré après remédiation reste par défaut '{vigilance}' en attente de l’avis IA."
    )



def build_simulated_expected_vigilance(row: pd.Series) -> str:
    current = str(review_vigilance_regime(row)[0] or "Vigilance Modérée").strip()
    alerts = set(build_row_alert_labels(row))
    if not alerts:
        if current == "Vigilance Critique":
            return "Vigilance Élevée"
        if current == "Vigilance Élevée":
            return "Vigilance Modérée"
        if current == "Vigilance Modérée":
            return "Vigilance Allégée"
        if current == "Vigilance Allégée":
            return "Vigilance Aucune"
        return current

    major_alerts = {"Risque avéré", "Cross-border élevé", "Cash intensité élevée"}
    if alerts & major_alerts:
        if current in {"Vigilance Critique", "Vigilance Élevée"}:
            return current
        return "Vigilance Élevée"

    if current == "Vigilance Critique":
        return "Vigilance Élevée"
    if current == "Vigilance Élevée":
        return "Vigilance Modérée"
    if current == "Vigilance Modérée":
        return "Vigilance Allégée"
    if current == "Vigilance Allégée":
        return "Vigilance Allégée"
    return current


def build_review_trend(real_status: object, estimated_status: object) -> str:
    real_rank = VIGILANCE_RANK.get(str(real_status).strip(), 99)
    estimated_rank = VIGILANCE_RANK.get(str(estimated_status).strip(), 99)
    if estimated_rank < real_rank:
        return "S’aggrave"
    if estimated_rank > real_rank:
        return "S’améliore"
    return "Stable"


def review_trend_icon(trend_value: object) -> str:
    trend = str(trend_value or "").strip()
    if trend == "S’aggrave":
        return "🔴 ▲"
    if trend == "S’améliore":
        return "🟢 ▼"
    return "🟠 •"


def apply_manual_estimated_status(working_df: pd.DataFrame, selected_indices: list[int], estimated_status: str) -> tuple[pd.DataFrame, int]:
    result = working_df.copy()
    batch_idx = [int(i) for i in selected_indices if 0 <= int(i) < len(result)]
    if not batch_idx:
        return result, 0
    for idx in batch_idx:
        row_label = result.index[idx]
        result.at[row_label, REVIEW_SIM_EST_LABEL] = estimated_status
        result.at[row_label, REVIEW_SIM_TREND_LABEL] = build_review_trend(
            result.at[row_label, REVIEW_SIM_REAL_LABEL],
            result.at[row_label, REVIEW_SIM_EST_LABEL],
        )
    return result, len(batch_idx)


def build_review_simulation_working_table(df: pd.DataFrame) -> pd.DataFrame:
    base_columns = [
        SOC_COL,
        "SIREN",
        "Dénomination",
        REVIEW_SIM_REAL_LABEL,
        "Explique moi",
        REVIEW_SIM_AI_STRUCTURED_LABEL,
        REVIEW_SIM_TREND_LABEL,
        REVIEW_SIM_EST_LABEL,
        "Type de revue",
        "Date prochaine revue",
        "Alertes actives",
    ]
    if df is None or df.empty:
        return pd.DataFrame(columns=base_columns)

    scope = df.copy()
    next_review_series = scope.get("Date prochaine revue", pd.Series(index=scope.index, dtype="object"))
    scope["Date prochaine revue"] = next_review_series.apply(coerce_mixed_date)
    scope[REVIEW_SIM_REAL_LABEL] = scope.apply(lambda row: review_vigilance_regime(row)[0], axis=1)
    scope["Type de revue"] = scope[REVIEW_SIM_REAL_LABEL].apply(review_type_for_vigilance)
    scope["Alertes actives"] = scope.apply(lambda row: ", ".join(build_row_alert_labels(row)) or "Aucune", axis=1)

    store = load_review_simulation_store()
    if not store.empty:
        scope = scope.merge(store, on=KEY_COLUMNS, how="left")
    else:
        scope["Explique moi"] = ""
        scope[REVIEW_SIM_EST_LABEL] = ""
        scope[REVIEW_SIM_AI_STRUCTURED_LABEL] = ""
        scope["updated_at_utc"] = ""

    if "Explique moi" not in scope.columns:
        scope["Explique moi"] = ""
    scope["Explique moi"] = scope["Explique moi"].fillna("").astype(str)
    if REVIEW_SIM_EST_LABEL not in scope.columns:
        scope[REVIEW_SIM_EST_LABEL] = ""
    scope[REVIEW_SIM_EST_LABEL] = scope[REVIEW_SIM_EST_LABEL].fillna("").astype(str)
    if REVIEW_SIM_AI_STRUCTURED_LABEL not in scope.columns:
        scope[REVIEW_SIM_AI_STRUCTURED_LABEL] = ""
    scope[REVIEW_SIM_AI_STRUCTURED_LABEL] = scope[REVIEW_SIM_AI_STRUCTURED_LABEL].fillna("").astype(str)
    empty_expected = scope[REVIEW_SIM_EST_LABEL].str.strip().eq("")
    scope.loc[empty_expected, REVIEW_SIM_EST_LABEL] = scope.loc[empty_expected].apply(build_simulated_expected_vigilance, axis=1)
    scope[REVIEW_SIM_TREND_LABEL] = scope.apply(lambda row: build_review_trend(row.get(REVIEW_SIM_REAL_LABEL, ""), row.get(REVIEW_SIM_EST_LABEL, "")), axis=1)

    table = pd.DataFrame({
        SOC_COL: scope[SOC_COL],
        "SIREN": scope["SIREN"],
        "Dénomination": scope.get("Dénomination", pd.Series("", index=scope.index)),
        REVIEW_SIM_REAL_LABEL: scope[REVIEW_SIM_REAL_LABEL],
        "Explique moi": scope["Explique moi"],
        REVIEW_SIM_AI_STRUCTURED_LABEL: scope[REVIEW_SIM_AI_STRUCTURED_LABEL],
        REVIEW_SIM_TREND_LABEL: scope[REVIEW_SIM_TREND_LABEL],
        REVIEW_SIM_EST_LABEL: scope[REVIEW_SIM_EST_LABEL],
        "Type de revue": scope["Type de revue"],
        "Date prochaine revue": scope.get("Date prochaine revue", pd.Series(pd.NaT, index=scope.index)),
        "Alertes actives": scope["Alertes actives"],
    })
    table = table.sort_values(["Date prochaine revue", REVIEW_SIM_REAL_LABEL, "Dénomination"], kind="stable", na_position="last")
    return table.reset_index(drop=True)


def persist_review_simulation_subset(
    edited_df: pd.DataFrame,
    selected_indices: list[int] | None = None,
    pdf_source_df: pd.DataFrame | None = None,
    prompt_template: str = "",
) -> tuple[int, list[str]]:
    if edited_df is None or edited_df.empty:
        return 0, []

    target_df = edited_df.copy()
    if selected_indices is not None:
        valid_indices = [int(i) for i in selected_indices if 0 <= int(i) < len(target_df)]
        if not valid_indices:
            return 0, []
        target_df = target_df.iloc[valid_indices].copy()

    store = load_review_simulation_store()
    if store.empty:
        store = pd.DataFrame(columns=KEY_COLUMNS + [
            "Explique moi",
            REVIEW_SIM_EST_LABEL,
            REVIEW_SIM_AI_STRUCTURED_LABEL,
            "updated_at_utc",
        ])
    if REVIEW_SIM_AI_STRUCTURED_LABEL not in target_df.columns:
        target_df[REVIEW_SIM_AI_STRUCTURED_LABEL] = ""
    subset = target_df[[SOC_COL, "SIREN", "Explique moi", REVIEW_SIM_EST_LABEL, REVIEW_SIM_AI_STRUCTURED_LABEL]].copy()
    subset["Explique moi"] = subset["Explique moi"].fillna("").astype(str)
    subset[REVIEW_SIM_EST_LABEL] = subset[REVIEW_SIM_EST_LABEL].fillna("").astype(str)
    subset[REVIEW_SIM_AI_STRUCTURED_LABEL] = subset[REVIEW_SIM_AI_STRUCTURED_LABEL].fillna("").astype(str)
    subset = subset[subset["Explique moi"].str.strip().ne("") | subset[REVIEW_SIM_EST_LABEL].str.strip().ne("") | subset[REVIEW_SIM_AI_STRUCTURED_LABEL].str.strip().ne("")].copy()
    if not subset.empty:
        subset[SOC_COL] = normalize_societe_id(subset[SOC_COL])
        subset["SIREN"] = normalize_siren(subset["SIREN"])
        subset["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
        remaining = store.merge(subset[KEY_COLUMNS], on=KEY_COLUMNS, how="left", indicator=True)
        remaining = remaining[remaining["_merge"] == "left_only"].drop(columns=["_merge"])
        combined = pd.concat([remaining, subset], ignore_index=True)
        save_review_simulation_store(combined)

    pdf_scope = target_df.copy()
    if "Explique moi" not in pdf_scope.columns:
        return 0, []

    if pdf_source_df is None:
        explain_mask = pdf_scope["Explique moi"].fillna("").astype(str).str.strip().ne("")
        if explain_mask.any():
            try:
                base_source_df, indicators_source_df, _ = load_source_data()
                pdf_source_df = build_review_simulation_source_dataset(pdf_scope.loc[explain_mask].copy(), base_source_df, indicators_source_df)
            except Exception as exc:
                return 0, [f"PDF : impossible de charger les données source ({exc})"]

    return sync_review_simulation_pdfs(pdf_scope, source_df=pdf_source_df, prompt_template=prompt_template)


def apply_review_simulation_batch(working_df: pd.DataFrame, selected_indices: list[int], source_df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    result = working_df.copy()
    batch_idx = [int(i) for i in selected_indices[:10] if 0 <= int(i) < len(result)]
    if not batch_idx:
        return result, 0

    source = source_df.copy()
    source[SOC_COL] = normalize_societe_id(source[SOC_COL])
    source["SIREN"] = normalize_siren(source["SIREN"])

    for idx in batch_idx:
        row_label = result.index[idx]
        row = result.iloc[idx]
        soc = normalize_societe_id(pd.Series([row.get(SOC_COL, "")])).iloc[0]
        siren = normalize_siren(pd.Series([row.get("SIREN", "")])).iloc[0]
        match = source[(source[SOC_COL] == soc) & (source["SIREN"] == siren)]
        if match.empty:
            source_row = pd.Series({
                SOC_COL: soc,
                "SIREN": siren,
                "Dénomination": row.get("Dénomination", ""),
                "Vigilance": row.get(REVIEW_SIM_REAL_LABEL, ""),
                "Risque": "",
                "Statut EDD": "",
                "Date prochaine revue": row.get("Date prochaine revue"),
            })
        else:
            source_row = match.iloc[0]
        result.at[row_label, "Explique moi"] = build_simulated_review_explanation(source_row)
        result.at[row_label, REVIEW_SIM_EST_LABEL] = build_simulated_expected_vigilance(source_row)
        result.at[row_label, REVIEW_SIM_TREND_LABEL] = build_review_trend(
            result.at[row_label, REVIEW_SIM_REAL_LABEL],
            result.at[row_label, REVIEW_SIM_EST_LABEL],
        )
    return result, len(batch_idx)


def build_review_simulation_export_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    export_df = df.copy()
    if "Date prochaine revue" in export_df.columns:
        export_df["Date prochaine revue"] = export_df["Date prochaine revue"].apply(format_short_date)
    keep_cols = [
        SOC_COL,
        "SIREN",
        "Dénomination",
        REVIEW_SIM_REAL_LABEL,
        "Type de revue",
        "Date prochaine revue",
        "Alertes actives",
        "Explique moi",
        REVIEW_SIM_TREND_LABEL,
        REVIEW_SIM_EST_LABEL,
    ]
    export_df = export_df[[c for c in keep_cols if c in export_df.columns]].copy()
    return export_df.rename(
        columns={
            REVIEW_SIM_REAL_LABEL: REVIEW_SIM_REAL_DISPLAY_LABEL,
            REVIEW_SIM_EST_LABEL: REVIEW_SIM_EST_DISPLAY_LABEL,
            REVIEW_SIM_TREND_LABEL: REVIEW_SIM_TREND_DISPLAY_LABEL,
            "Date prochaine revue": REVIEW_SIM_NEXT_REVIEW_DISPLAY_LABEL,
        }
    )


def style_review_simulation_table(display_df: pd.DataFrame) -> pd.io.formats.style.Styler:
    def style_cell(column_name: str, value: object) -> str:
        base = "padding: 0.42rem 0.55rem; text-align: center; vertical-align: middle; border-bottom: 1px solid rgba(22,58,89,0.08);"
        if column_name == "SIREN":
            return base + "color: #163A59; font-weight: 800; text-decoration: underline;"
        if column_name == "Dénomination":
            return base + "font-weight: 700; color: #163A59; text-align:left;"
        if column_name in {REVIEW_SIM_REAL_LABEL, REVIEW_SIM_EST_LABEL, REVIEW_SIM_REAL_DISPLAY_LABEL, REVIEW_SIM_EST_DISPLAY_LABEL}:
            bg, fg = status_palette(value, "vigilance")
            return base + f"background-color:{bg}; color:{fg}; font-weight:700; border-radius:999px;"
        if column_name in {REVIEW_SIM_TREND_LABEL, REVIEW_SIM_TREND_DISPLAY_LABEL}:
            text = str(value).strip()
            if text.startswith("🔴") or text == "S’aggrave":
                return base + "background-color: rgba(217,45,32,0.10); color:#B42318; font-weight:700;"
            if text.startswith("🟢") or text == "S’améliore":
                return base + "background-color: rgba(18,183,106,0.10); color:#027A48; font-weight:700;"
            return base + "background-color: rgba(249,115,22,0.10); color:#B54708; font-weight:700;"
        if column_name == "Explique moi":
            text = str(value).strip()
            if text:
                return base + "background-color: rgba(22,58,89,0.06); color:#163A59; font-weight:700; letter-spacing:0.01em; text-decoration: underline; text-underline-offset: 0.12rem;"
            return base + "background-color: transparent; color: transparent;"
        if column_name in {"Date prochaine revue", REVIEW_SIM_NEXT_REVIEW_DISPLAY_LABEL}:
            return base + "font-weight:600; color:#163A59; white-space:nowrap; font-size:0.94rem;"
        return base

    zebra = pd.DataFrame("", index=display_df.index, columns=display_df.columns)
    zebra.iloc[1::2, :] = "background-color: rgba(22,58,89,0.025);"
    styled = display_df.style
    styled = styled.set_table_styles([
        {"selector": "thead th", "props": [("background-color", "#163A59"), ("color", "white"), ("font-weight", "700"), ("text-transform", "uppercase"), ("font-size", "0.76rem"), ("letter-spacing", "0.08em"), ("text-align", "center"), ("border-bottom", "0")]},
        {"selector": "thead tr", "props": [("background-color", "#163A59")]},
        {"selector": "tbody td", "props": [("background-color", "#ffffff"), ("text-align", "center")]},
    ])
    styled = styled.apply(lambda _: zebra, axis=None)
    styled = styled.apply(lambda s: [style_cell(s.name, v) for v in s], axis=0)
    return styled


def render_review_status_gauges(df: pd.DataFrame) -> None:
    if df is None or df.empty:
        return

    total = max(int(df["SIREN"].nunique()), 1)
    statuses = ["Vigilance Critique", "Vigilance Élevée", "Vigilance Modérée", "Vigilance Allégée"]

    def format_pct(value: float) -> str:
        return f"{value * 100:.1f}".replace(".", ",") + " %"

    def build_card(status_label: str, count: int, total_count: int, kicker: str) -> str:
        pct = (count / total_count) if total_count else 0.0
        bg, fg = status_palette(status_label, "vigilance")
        width = round(pct * 100) if count else 0
        return (
            "<div style='background:#FFFFFF; border:1px solid rgba(22,58,89,0.08); border-radius:18px; padding:0.9rem 1rem; box-shadow:0 10px 24px rgba(22,58,89,0.05); min-height:138px;'>"
            f"<div style='font-size:0.72rem; text-transform:uppercase; letter-spacing:0.08em; color:#5B7084; margin-bottom:0.25rem;'>{escape(kicker)}</div>"
            f"<div style='display:inline-flex; padding:0.22rem 0.55rem; border-radius:999px; background:{bg}; color:{fg}; font-weight:700; font-size:0.78rem; margin-bottom:0.55rem;'>{escape(status_label)}</div>"
            f"<div style='font-size:1.55rem; font-weight:800; color:#163A59; line-height:1.1;'>{count}</div>"
            f"<div style='font-size:0.82rem; color:#5B7084; margin-top:0.15rem;'>{count} société(s) • {format_pct(pct)}</div>"
            f"<div style='margin-top:0.7rem; height:8px; border-radius:999px; background:#EAF2FB; overflow:hidden;'><div style='width:{width}%; min-width:{'6px' if count else '0'}; height:100%; background:{bg};'></div></div>"
            "</div>"
        )

    real_cards = []
    est_cards = []
    for label in statuses:
        real_count = int(df.loc[df[REVIEW_SIM_REAL_LABEL].astype(str).eq(label), "SIREN"].nunique())
        est_count = int(df.loc[df[REVIEW_SIM_EST_LABEL].astype(str).eq(label), "SIREN"].nunique())
        real_cards.append(build_card(label, real_count, total, "Statuts réels"))
        est_cards.append(build_card(label, est_count, total, "Statuts estimés"))

    grid_style = "display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:0.85rem;"
    st.markdown(f"<div style='{grid_style} margin:0.2rem 0 1.15rem 0;'>" + "".join(real_cards) + "</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='height:0.45rem;'></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='{grid_style} margin:0.0rem 0 0.95rem 0;'>" + "".join(est_cards) + "</div>", unsafe_allow_html=True)


def format_review_simulation_vigilance_filter_option(label: str) -> str:
    label_text = str(label or "").strip()
    if not label_text:
        return ""
    short_label = label_text.replace("Vigilance ", "").strip()
    return f"{status_emoji(label_text, 'vigilance')} {short_label}"


def review_simulation_short_vigilance_label(value: object) -> str:
    label_text = str(value or "").strip()
    if not label_text:
        return ""
    return label_text.replace("Vigilance ", "").strip()


def render_review_simulation_vigilance_legend(status_labels: list[str]) -> None:
    chips: list[str] = []
    for label in status_labels:
        bg, fg = status_palette(label, "vigilance")
        short_label = escape(str(label).replace("Vigilance ", "").strip())
        chips.append(
            f'<span style="display:inline-flex; align-items:center; justify-content:center; padding:0.20rem 0.62rem; border-radius:999px; background:{bg}; color:{fg}; font-family:Source Sans Pro,sans-serif; font-size:0.82rem; font-weight:700; line-height:1; box-shadow: inset 0 0 0 1px rgba(22,58,89,0.04);">{short_label}</span>'
        )
    if chips:
        st.markdown(
            "<div style='display:flex; flex-wrap:wrap; gap:0.45rem; margin:0.18rem 0 0.72rem 0;'>" + "".join(chips) + "</div>",
            unsafe_allow_html=True,
        )


def review_sim_selection_keys(df: pd.DataFrame, row_indices: list[int]) -> list[str]:
    if df is None or df.empty or not row_indices:
        return []
    result: list[str] = []
    for idx in row_indices:
        if idx < 0 or idx >= len(df):
            continue
        row = df.iloc[idx]
        soc = normalize_societe_id(pd.Series([row.get(SOC_COL, "")])).iloc[0]
        siren = normalize_siren(pd.Series([row.get("SIREN", "")])).iloc[0]
        if pd.notna(soc) and pd.notna(siren):
            result.append(f"{soc}|{siren}")
    return list(dict.fromkeys(result))


def review_sim_rows_from_selection(df: pd.DataFrame, selected_keys: list[str]) -> list[int]:
    if df is None or df.empty or not selected_keys:
        return []
    normalized = df[[SOC_COL, "SIREN"]].copy()
    normalized[SOC_COL] = normalize_societe_id(normalized[SOC_COL])
    normalized["SIREN"] = normalize_siren(normalized["SIREN"])
    key_series = normalized[SOC_COL].fillna("").astype(str) + "|" + normalized["SIREN"].fillna("").astype(str)
    allowed = set(selected_keys)
    return [int(i) for i, key in enumerate(key_series.tolist()) if key in allowed]


def build_review_sim_client_href(societe_id: object, siren: object) -> str:
    societe_text = str(societe_id or "").strip()
    siren_text = str(siren or "").strip()
    if not societe_text or not siren_text:
        return "?view=revues-simulations"
    return f"?view=client&societe={quote_plus(societe_text)}&siren={quote_plus(siren_text)}"


def build_review_sim_explain_href(societe_id: object, siren: object, has_content: bool) -> str:
    if not has_content:
        return "?view=revues-simulations#○"
    societe_text = str(societe_id or "").strip()
    siren_text = str(siren or "").strip()
    if not societe_text or not siren_text:
        return "?view=revues-simulations#○"
    return f"?view=revues-simulations&explain_societe={quote_plus(societe_text)}&explain_siren={quote_plus(siren_text)}#●"


def _get_review_simulation_explain_payload(df: pd.DataFrame) -> dict[str, str] | None:
    target = st.session_state.get("review_sim_explain_target")
    if not isinstance(target, dict):
        return None

    explain_societe = str(target.get("societe", "") or "").strip()
    explain_siren = str(target.get("siren", "") or "").strip()
    if not explain_societe or not explain_siren or df is None or df.empty:
        return None

    scope = df.copy()
    if SOC_COL not in scope.columns or "SIREN" not in scope.columns or "Explique moi" not in scope.columns:
        return None

    scope["__societe_norm"] = normalize_societe_id(scope[SOC_COL]).fillna("").astype(str)
    scope["__siren_norm"] = normalize_siren(scope["SIREN"]).fillna("").astype(str)
    target_societe = normalize_societe_id(pd.Series([explain_societe])).fillna("").astype(str).iloc[0]
    target_siren = normalize_siren(pd.Series([explain_siren])).fillna("").astype(str).iloc[0]
    match = scope.loc[(scope["__societe_norm"] == target_societe) & (scope["__siren_norm"] == target_siren)]
    if match.empty:
        st.session_state.pop("review_sim_explain_target", None)
        return None

    row = match.iloc[0]
    explain_text = str(row.get("Explique moi", "") or "").strip()
    if not explain_text:
        st.session_state.pop("review_sim_explain_target", None)
        return None

    return {
        "denomination": str(row.get("Dénomination", "") or "").strip(),
        "siren": str(row.get("SIREN", "") or "").strip(),
        "content": explain_text,
    }


if hasattr(st, "dialog"):
    @st.dialog("Explique moi", width="large")
    def _render_review_simulation_explain_dialog(payload: dict[str, str]) -> None:
        denomination = escape(str(payload.get("denomination", "") or "").strip())
        siren_label = escape(str(payload.get("siren", "") or "").strip())
        content_html = escape(str(payload.get("content", "") or "").strip()).replace("\n", "<br>")
        st.markdown(
            f"""
            <div style="margin:0.1rem 0 0.65rem 0;">
                <div style="color:#5B7084;font-family:Source Sans Pro,sans-serif;font-size:0.95rem;line-height:1.35;">{denomination} • {siren_label}</div>
            </div>
            <style>
            .review-explain-dialog-body {{
                max-height: 66vh;
                overflow-y: auto;
                padding: 0.15rem 0.1rem 0.2rem 0.1rem;
                color: #163A59;
                font-family: "Source Sans Pro", sans-serif;
                font-size: 1rem;
                line-height: 1.62;
                white-space: normal;
            }}
            </style>
            <div class="review-explain-dialog-body">{content_html}</div>
            """,
            unsafe_allow_html=True,
        )
        close_cols = st.columns([6, 1], gap="small")
        with close_cols[1]:
            if st.button("Fermer", key="review_explain_close_btn", use_container_width=True):
                st.session_state.pop("review_sim_explain_target", None)
                st.rerun()
else:
    def _render_review_simulation_explain_dialog(payload: dict[str, str]) -> None:
        denomination = escape(str(payload.get("denomination", "") or "").strip())
        siren_label = escape(str(payload.get("siren", "") or "").strip())
        content_html = escape(str(payload.get("content", "") or "").strip()).replace("\n", "<br>")
        head_cols = st.columns([7, 1], gap="small")
        with head_cols[0]:
            st.markdown(
                f"""
                <div style="margin:0.35rem 0 0.25rem 0;">
                    <div style="color:#163A59;font-family:Source Sans Pro,sans-serif;font-size:1.18rem;font-weight:700;line-height:1.2;">Explique moi</div>
                    <div style="margin-top:0.12rem;color:#5B7084;font-family:Source Sans Pro,sans-serif;font-size:0.92rem;line-height:1.35;">{denomination} • {siren_label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with head_cols[1]:
            st.markdown("<div style='height:0.25rem;'></div>", unsafe_allow_html=True)
            if st.button("Fermer", key="review_explain_close_btn", type="secondary", use_container_width=True):
                st.session_state.pop("review_sim_explain_target", None)
                st.rerun()
        st.markdown(
            f"""
            <style>
            .review-explain-panel {{
                border: 1px solid rgba(22,58,89,0.10);
                border-radius: 18px;
                background: #FFFFFF;
                box-shadow: 0 18px 45px rgba(15, 23, 42, 0.10);
                overflow: hidden;
                margin: 0.15rem 0 0.9rem 0;
            }}
            .review-explain-panel__body {{
                max-height: 68vh;
                overflow-y: auto;
                padding: 1.1rem 1.2rem 1.2rem 1.2rem;
                color: #163A59;
                font-family: "Source Sans Pro", sans-serif;
                font-size: 1rem;
                line-height: 1.62;
                white-space: normal;
            }}
            </style>
            <div class="review-explain-panel">
                <div class="review-explain-panel__body">{content_html}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_review_simulation_explain_overlay(df: pd.DataFrame) -> None:
    payload = _get_review_simulation_explain_payload(df)
    if payload is None:
        return
    _render_review_simulation_explain_dialog(payload)


def review_simulation_emit_feedback() -> None:
    notice = str(st.session_state.pop("review_sim_notice", "") or "").strip()
    warning = str(st.session_state.pop("review_sim_warning", "") or "").strip()
    toast_fn = getattr(st, "toast", None)
    if notice:
        if callable(toast_fn):
            toast_fn(notice, icon="✅")
        else:
            st.success(notice)
    if warning:
        if callable(toast_fn):
            toast_fn(warning, icon="⚠️")
        else:
            st.warning(warning)


def review_simulation_download_button(label: str, **kwargs):
    try:
        if "on_click" in inspect.signature(st.download_button).parameters:
            kwargs.setdefault("on_click", "ignore")
    except Exception:
        pass
    return st.download_button(label, **kwargs)


def build_review_simulation_detail_df(portfolio: pd.DataFrame, review_df: pd.DataFrame, selected_keys: list[str]) -> pd.DataFrame:
    if portfolio is None or portfolio.empty or review_df is None or review_df.empty:
        return pd.DataFrame()
    source = portfolio.copy()
    source[SOC_COL] = normalize_societe_id(source[SOC_COL])
    source["SIREN"] = normalize_siren(source["SIREN"])
    review_norm = review_df[[SOC_COL, "SIREN"]].copy()
    review_norm[SOC_COL] = normalize_societe_id(review_norm[SOC_COL])
    review_norm["SIREN"] = normalize_siren(review_norm["SIREN"])
    all_keys = review_norm[SOC_COL].fillna("").astype(str) + "|" + review_norm["SIREN"].fillna("").astype(str)
    target_keys = list(dict.fromkeys(selected_keys or all_keys.tolist()))
    source_keys = source[SOC_COL].fillna("").astype(str) + "|" + source["SIREN"].fillna("").astype(str)
    detail_df = source.loc[source_keys.isin(set(target_keys))].copy()
    if detail_df.empty:
        return detail_df
    detail_df = detail_df[[c for c in DISPLAY_COLUMNS if c in detail_df.columns]].copy()
    sort_cols = [c for c in ["Date prochaine revue", "Vigilance", "Dénomination"] if c in detail_df.columns]
    if sort_cols:
        detail_df = detail_df.sort_values(sort_cols, kind="stable", na_position="last")
    return detail_df.reset_index(drop=True)

def render_review_simulation_table(df: pd.DataFrame, key: str) -> list[int]:
    def _first_selected_cell(cells: object) -> tuple[int, str] | None:
        if not cells:
            return None
        cell = list(cells)[0]
        if isinstance(cell, dict):
            row_idx = cell.get("row")
            col_name = cell.get("column")
        elif isinstance(cell, (list, tuple)) and len(cell) >= 2:
            row_idx, col_name = cell[0], cell[1]
        else:
            return None
        try:
            row_idx_int = int(row_idx)
        except Exception:
            return None
        col_name_text = str(col_name or "").strip()
        if not col_name_text:
            return None
        return row_idx_int, col_name_text

    raw_df = df.copy().reset_index(drop=True)
    display_df = raw_df.copy()
    display_df["Date prochaine revue"] = display_df["Date prochaine revue"].apply(format_short_date)
    display_df["Explique moi"] = display_df["Explique moi"].apply(
        lambda value: "a lire" if str(value or "").strip() else ""
    )
    if "SIREN" in display_df.columns:
        display_df["SIREN"] = display_df["SIREN"].apply(lambda value: f"↗ {display_value(value)}")
    for status_col in (REVIEW_SIM_REAL_LABEL, REVIEW_SIM_EST_LABEL):
        if status_col in display_df.columns:
            display_df[status_col] = display_df[status_col].apply(review_simulation_short_vigilance_label)
    display_df[REVIEW_SIM_TREND_LABEL] = display_df[REVIEW_SIM_TREND_LABEL].apply(review_trend_icon)

    column_order = [
        SOC_COL,
        "SIREN",
        "Dénomination",
        REVIEW_SIM_REAL_LABEL,
        "Explique moi",
        REVIEW_SIM_TREND_LABEL,
        REVIEW_SIM_EST_LABEL,
        "Date prochaine revue",
    ]
    display_df = display_df[[c for c in column_order if c in display_df.columns]].copy()
    display_df = display_df.rename(
        columns={
            REVIEW_SIM_REAL_LABEL: REVIEW_SIM_REAL_DISPLAY_LABEL,
            REVIEW_SIM_TREND_LABEL: REVIEW_SIM_TREND_DISPLAY_LABEL,
            REVIEW_SIM_EST_LABEL: REVIEW_SIM_EST_DISPLAY_LABEL,
            "Date prochaine revue": REVIEW_SIM_NEXT_REVIEW_DISPLAY_LABEL,
        }
    )

    column_config = {
        SOC_COL: st.column_config.TextColumn("Société", width="small"),
        "SIREN": st.column_config.TextColumn(
            "SIREN",
            width="small",
            help="Cliquez sur une cellule SIREN pour ouvrir la fiche client dans l’application.",
        ),
        "Dénomination": st.column_config.TextColumn("Dénomination", width="medium"),
        REVIEW_SIM_REAL_DISPLAY_LABEL: st.column_config.TextColumn(REVIEW_SIM_REAL_DISPLAY_LABEL, width="small"),
        "Explique moi": st.column_config.TextColumn(
            "Explique moi",
            width="small",
            help="Colonne vide : aucun contenu • a lire : cliquez pour ouvrir le contenu en grand format.",
        ),
        REVIEW_SIM_TREND_DISPLAY_LABEL: st.column_config.TextColumn(REVIEW_SIM_TREND_DISPLAY_LABEL, width="small"),
        REVIEW_SIM_EST_DISPLAY_LABEL: st.column_config.TextColumn(REVIEW_SIM_EST_DISPLAY_LABEL, width="small"),
        REVIEW_SIM_NEXT_REVIEW_DISPLAY_LABEL: st.column_config.TextColumn(REVIEW_SIM_NEXT_REVIEW_DISPLAY_LABEL, width="medium"),
    }

    event = st.dataframe(
        style_review_simulation_table(display_df),
        width="stretch",
        height=min(660, 240 + 38 * max(len(display_df), 1)),
        hide_index=True,
        column_order=list(display_df.columns),
        column_config=column_config,
        on_select="rerun",
        selection_mode=("multi-row", "single-cell"),
        row_height=42,
        key=key,
    )
    selected_rows: list[int] = []
    selected_cells: list[object] = []
    if event is not None:
        try:
            selected_rows = [int(i) for i in event.selection.get("rows", [])]
        except Exception:
            selected_rows = []
        try:
            selected_cells = list(event.selection.get("cells", []))
        except Exception:
            selected_cells = []

    selected_cell = _first_selected_cell(selected_cells)
    if selected_cell is None:
        st.session_state.pop("review_sim_last_cell_action", None)
        return selected_rows

    row_idx, col_name = selected_cell
    if row_idx < 0 or row_idx >= len(raw_df):
        return selected_rows

    row = raw_df.iloc[row_idx]
    societe_id = str(row.get(SOC_COL, "") or "").strip()
    siren = str(row.get("SIREN", "") or "").strip()
    action_token = f"{row_idx}:{col_name}:{societe_id}|{siren}"
    last_action_token = str(st.session_state.get("review_sim_last_cell_action", "") or "").strip()
    if action_token == last_action_token:
        return selected_rows

    if col_name == "SIREN" and societe_id and siren:
        st.session_state["review_sim_last_cell_action"] = action_token
        open_client_detail(societe_id, siren)
        st.rerun()

    if col_name == "Explique moi":
        explain_text = str(row.get("Explique moi", "") or "").strip()
        if explain_text and societe_id and siren:
            st.session_state["review_sim_last_cell_action"] = action_token
            st.session_state["review_sim_explain_target"] = {"societe": societe_id, "siren": siren}
            st.rerun()

    return selected_rows


def render_review_simulation_glossary_expander() -> None:
    glossary_rows = [
        ["Clé Agent IA", "Clé Gemini saisie localement pour lancer les analyses IA de l’écran. Elle n’est pas sauvegardée."],
        ["Prompt Agent IA", "Prompt standard modifiable utilisé pour construire l’analyse IA et les PDF structurés générés depuis l’écran."],
        ["Recherche SIREN / dénomination", "Sélecteur permettant de restreindre l’écran à un SIREN unique à partir du SIREN ou de la dénomination."],
        ["Statuts réels", "Première rangée de jauges : répartition des sociétés par statut de vigilance réel sur le périmètre recherché."],
        ["Statuts estimés", "Deuxième rangée de jauges : répartition des sociétés par statut de vigilance estimé après remédiation sur le périmètre recherché."],
        ["Statut de vigilance réel", "Régime de vigilance normalisé à partir de la colonne Vigilance du portefeuille."],
        ["Statut réel", "Libellé court affiché dans le tableau pour le statut de vigilance réel."],
        ["Statut de vigilance estimé après remédiation", "Statut cible retenu pour la revue. Il peut provenir d’une valeur déjà sauvegardée, d’une simulation par défaut, d’une mise à jour manuelle ou de l’Agent IA."],
        ["Statut estimé", "Libellé court affiché dans le tableau pour le statut de vigilance estimé après remédiation."],
        ["Indicateur de tendance", "Comparaison entre le statut réel et le statut estimé : S’aggrave, Stable ou S’améliore."],
        ["Tendance", "Icône courte de l’indicateur de tendance dans le tableau : 🔴 ▲, 🟠 • ou 🟢 ▼."],
        ["Type de revue", "Libellé opérationnel dérivé du statut réel : revue critique immédiate, revue renforcée, revue ciblée, revue allégée de mise à jour ou revue standard."],
        ["Prochaine revue", "Date de prochaine revue actuellement portée par le dossier et affichée dans le tableau."],
        ["Alertes actives", "Liste textuelle des alertes calculées du dossier, concaténées dans un ordre fixe."],
        ["Explique moi", "Restitution textuelle de l’analyse opérationnelle de revue. Le tableau affiche ‘a lire’ quand un contenu existe."],
        ["Analyse IA structurée", "JSON structuré renvoyé par l’Agent IA et réutilisé pour les PDF de revue et de classification."],
        ["Référentiel des indicateurs actifs", "Expander affichant le référentiel durci transmis à l’Agent IA ; le socle BeCLM est imposé et seule la colonne ‘Sens métier de l’indicateur pour l’IA’ reste modifiable depuis l’écran."],
        ["PDF(s)", "Téléchargement du PDF du SIREN sélectionné, ou d’un ZIP quand plusieurs PDF existent déjà pour ce dossier."],
        ["ZIP PDF", "Téléchargement de tous les PDF structurés déjà générés sur le périmètre courant."],
        ["CSV", "Export du tableau visible de l’écran Revues & Simulations après application des filtres."],
    ]

    calc_rows = [
        [
            "Base de l’écran Revues & Simulations",
            "Table de travail construite à partir du portefeuille filtré, enrichie avec le magasin persistant des revues (‘Explique moi’, statut estimé, analyse IA structurée), puis triée par Date prochaine revue, Statut de vigilance réel et Dénomination.",
            "SIREN du périmètre courant",
            "La table est reconstruite à chaque rendu de l’écran à partir du portefeuille déjà filtré en amont.",
        ],
        [
            "Recherche SIREN / dénomination",
            "Sélecteur alimenté par la liste unique [SIREN, Dénomination]. Une fois un choix fait, le filtre appliqué est un match exact sur le SIREN retenu.",
            "Périmètre recherché",
            "Les jauges et le tableau aval se recalculent uniquement sur ce périmètre recherché.",
        ],
        [
            "Jauges Statuts réels",
            "Pour chaque statut de vigilance (Critique, Élevée, Modérée, Allégée) : count(SIREN uniques dont le statut réel == valeur) ; % = count / total SIREN uniques du périmètre recherché.",
            "Périmètre recherché",
            "Calculé avant le multiselect ‘Filtrer sur le statut de vigilance réel’.",
        ],
        [
            "Jauges Statuts estimés",
            "Pour chaque statut de vigilance (Critique, Élevée, Modérée, Allégée) : count(SIREN uniques dont le statut estimé == valeur) ; % = count / total SIREN uniques du périmètre recherché.",
            "Périmètre recherché",
            "Même assiette que les jauges de statuts réels.",
        ],
        [
            "Statut de vigilance réel",
            "Normalisation de la colonne ‘Vigilance’ du portefeuille : texte contenant critique → Vigilance Critique ; élevée → Vigilance Élevée ; modérée → Vigilance Modérée ; allégée → Vigilance Allégée ; aucune → Vigilance Aucune ; à défaut → Vigilance Aucune.",
            "Société",
            "Cette valeur alimente aussi le Type de revue et la comparaison de tendance.",
        ],
        [
            "Type de revue",
            "Mapping direct sur le statut réel : Critique → Revue critique immédiate ; Élevée → Revue renforcée ; Modérée → Revue ciblée ; Allégée → Revue allégée de mise à jour ; Aucune → Revue standard.",
            "Société",
            "Aucun autre critère n’entre dans ce calcul.",
        ],
        [
            "Alertes actives",
            "Concaténation, dans cet ordre, des alertes suivantes quand elles sont présentes : Justificatifs incomplets ; Sans prochaine revue ; Revue trop ancienne ; Cross-border élevé ; Cash intensité élevée ; Risque avéré ou Risque potentiel ; EDD <statut> si le statut EDD n’est ni ‘Validée’, ni ‘Non requise’, ni ‘Aucun’.",
            "Société",
            "Si aucune alerte n’est active, la valeur affichée est ‘Aucune’.",
        ],
        [
            "Détail des alertes calculées",
            "Justificatifs incomplets = Alerte justificatif incomplet == 1 ; Sans prochaine revue = Alerte sans prochaine revue == 1 ; Revue trop ancienne = Alerte revue trop ancienne == 1 ; Cross-border élevé = Alerte cross-border élevé == 1 ; Cash intensité élevée = Alerte cash intensité élevée == 1.",
            "Société",
            "Les colonnes d’alerte proviennent du portefeuille préparé en amont et sont simplement relues ici.",
        ],
        [
            "Statut estimé par défaut",
            "Si aucun statut estimé n’est déjà sauvegardé, la simulation applique ces règles : sans alerte, on baisse d’un cran vers Aucune ; avec alerte majeure (Risque avéré, Cross-border élevé, Cash intensité élevée), on conserve Critique/Élevée ou on force Élevée ; sinon Critique → Élevée, Élevée → Modérée, Modérée → Allégée, Allégée → Allégée, Aucune → Aucune.",
            "Société",
            "Cette simulation par défaut est remplacée si une valeur manuelle ou IA existe déjà.",
        ],
        [
            "Filtre sur le statut de vigilance réel",
            "working_df = working_df[Statut de vigilance réel ∈ sélection du multiselect] ; si aucune valeur n’est sélectionnée, l’écran est vidé.",
            "Tableau Revues & Simulations",
            "Ce filtre agit après les jauges et avant la sélection du tableau.",
        ],
        [
            "Indicateur de tendance",
            "Comparaison des rangs de vigilance : Critique = 0, Élevée = 1, Modérée = 2, Allégée = 3, Aucune = 4. Si rang estimé < rang réel → S’aggrave ; si rang estimé > rang réel → S’améliore ; sinon → Stable.",
            "Société",
            "Le tableau affiche ensuite l’icône correspondante : 🔴 ▲, 🟠 • ou 🟢 ▼.",
        ],
        [
            "Appliquer",
            "Pour toutes les lignes sélectionnées : mise à jour du Statut de vigilance estimé après remédiation avec la valeur choisie dans la liste, puis recalcul immédiat de la tendance.",
            "Sélection courante",
            "La sélection est mémorisée par la clé [Société|SIREN] jusqu’au clic sur ‘Effacer’.",
        ],
        [
            "Agent IA",
            f"Traitement du lot courant sur au plus {GEMINI_MAX_BATCH_SIZE} SIREN sélectionnés. L’agent reçoit un payload structuré avec contexte_simulation, alertes_calculees, donnees_base_source, indicateurs_source, indicateurs_source_groupes, referentiel_indicateurs_actifs, le cadre méthodologique BeCLM et les garde-fous du référentiel durci ; il renseigne ‘Explique moi’, l’analyse IA structurée, le statut estimé et déclenche la génération / mise à jour des PDF, avec un contrôle qualité et une éventuelle seconde tentative automatique.",
            "Sélection courante",
            "Le bouton est désactivé sans sélection ou sans clé Agent IA.",
        ],
        [
            "Explique moi (affichage)",
            "Dans le tableau, le contenu textuel est remplacé par ‘a lire’ si la cellule contient du texte ; un clic ouvre la restitution complète en grand format.",
            "Tableau visible",
            "Le texte complet reste stocké dans le magasin persistant des revues.",
        ],
        [
            "Référentiel des indicateurs actifs",
            "Table construite sur un socle durci BeCLM intégré au script. Si un fichier Excel de référentiel est disponible, seuls les indicateurs additionnels hors socle peuvent le compléter au chargement ; dans l’écran, seule la colonne ‘Sens métier de l’indicateur pour l’IA’ est éditable et les colonnes Famille et Indicateur d’alerte restent figées.",
            "Écran Revues & Simulations",
            "Le référentiel édité dans la session est renvoyé à l’Agent IA dans le bloc ‘referentiel_indicateurs_actifs’, accompagné d’un cadre méthodologique BeCLM et de garde-fous globaux et par indicateur ; l’appel Gemini peut être rejoué automatiquement une fois si la première réponse n’est pas assez conforme au référentiel durci.",
        ],
        [
            "Export CSV",
            "Export du tableau visible après filtres, avec conversion de la date en format court et conservation des colonnes : Société, SIREN, Dénomination, Statut réel, Type de revue, Prochaine revue, Alertes actives, Explique moi, Tendance, Statut estimé.",
            "Périmètre filtré visible",
            "L’export reflète l’écran courant, pas l’ensemble du portefeuille.",
        ],
        [
            "PDF(s) / ZIP PDF",
            "PDF(s) télécharge le document unique du SIREN sélectionné, ou un ZIP si plusieurs PDF existent déjà pour ce dossier ; ZIP PDF agrège tous les PDF structurés disponibles sur le périmètre recherché.",
            "Documents déjà générés",
            "La disponibilité dépend de la présence effective des PDF sur le serveur et de l’installation de ReportLab.",
        ],
    ]

    with st.expander("Glossaire & calculs de l’écran Revues & Simulations", expanded=False):
        st.caption("Aide documentaire de lecture. Ce bloc n’a aucun impact sur les calculs ni sur les exports de l’écran.")

        glossary_tab, calculation_tab = st.tabs(["Glossaire", "Calculs"])

        with glossary_tab:
            st.dataframe(
                pd.DataFrame(glossary_rows, columns=["Terme", "Définition"]),
                use_container_width=True,
                hide_index=True,
                height=540,
            )

        with calculation_tab:
            render_reference_table(
                pd.DataFrame(calc_rows, columns=["Indicateur", "Calcul / règle", "Périmètre", "Note"]),
                column_min_widths=["260px", "760px", "210px", "520px"],
            )



def render_review_simulation_indicator_reference_expander() -> None:
    ensure_review_simulation_indicator_reference_state()
    reference_df = get_review_simulation_indicator_reference_df()
    source_label = str(st.session_state.get(REVIEW_SIM_INDICATOR_REFERENCE_SOURCE_STATE, INDICATOR_REFERENCE_DEFAULT_SOURCE_LABEL))

    with st.expander("Référentiel des indicateurs actifs (sens métier pour l’IA)", expanded=False):
        st.caption(
            "Ce tableau sert de référentiel d’interprétation métier durci pour l’Agent IA sur l’écran Revues & Simulations. "
            "Le socle durci BeCLM est imposé dans l’application ; seule la colonne ‘Sens métier de l’indicateur pour l’IA’ est modifiable depuis l’écran."
        )
        st.caption(source_label)
        edited_df = st.data_editor(
            reference_df,
            key=REVIEW_SIM_INDICATOR_REFERENCE_EDITOR_KEY,
            hide_index=True,
            use_container_width=True,
            num_rows="fixed",
            disabled=["Famille", "Indicateur d’alerte"],
            column_config={
                "Famille": st.column_config.TextColumn("Famille", width="medium"),
                "Indicateur d’alerte": st.column_config.TextColumn("Indicateur d’alerte", width="medium"),
                "Sens métier de l’indicateur pour l’IA": st.column_config.TextColumn(
                    "Sens métier de l’indicateur pour l’IA",
                    width="large",
                ),
            },
            height=760,
        )
        st.session_state[REVIEW_SIM_INDICATOR_REFERENCE_STATE] = merge_indicator_reference_with_hard_defaults(pd.DataFrame(edited_df), prefer_loaded_for_known=True)
        st.caption("Les modifications sont conservées dans la session courante, ajoutées au contexte envoyé à l’Agent IA et restent encadrées par le socle durci BeCLM.")


def render_review_simulations_screen(portfolio: pd.DataFrame, user: dict) -> None:
    render_home_hero("Revues & Simulations")
    nav = render_primary_navigation("review_simulations")
    if nav == "portfolio":
        open_portfolio_view()
        st.rerun()
    if nav == "analysis":
        open_analysis_view()
        st.rerun()
    if nav == "review_dates":
        open_review_dates_view()
        st.rerun()
    if nav == "evolution":
        open_evolution_view()
        st.rerun()

    ensure_review_simulation_indicator_reference_state()
    base_df = build_review_simulation_working_table(portfolio)
    if base_df.empty:
        st.info("Aucun SIREN disponible pour préparer une revue sur le périmètre courant.")
        return

    default_prompt = """Tu es l’agent IA BeCLM spécialisé en revue KYC / EDD / LCB-FT.
Tu reçois en entrée la fiche client complète disponible pour le SIREN analysé, structurée au minimum dans les blocs suivants :
- contexte_simulation
- donnees_base_source
- indicateurs_source
- indicateurs_source_groupes
- referentiel_indicateurs_actifs
- garde_fous_referentiel_globaux
- garde_fous_referentiel_indicateurs
- cadre_methodologique_beclm
- alertes_calculees

Consignes impératives :
1. Tu dois fonder ton analyse sur l’ensemble des données de la fiche client disponibles en entrée.
2. Tu dois utiliser de façon prioritaire :
   - toutes les données de base de la société,
   - l’ensemble des indicateurs,
   - les alertes calculées,
   - le référentiel durci BeCLM, ses garde-fous et le cadre méthodologique BeCLM.
3. Le référentiel BeCLM prévaut sur toute interprétation libre : tu dois t’appuyer explicitement sur le sens métier de chaque indicateur.
4. Tu ne dois pas faire une analyse générique. Tu dois t’appuyer explicitement sur les informations concrètes de la fiche client.
5. Les valeurs détaillées des indicateurs, les seuils de déclenchement, les pondérations et les paramétrages internes BeCLM ne te sont pas communiqués. Tu ne peux donc ni les deviner ni raisonner comme s’ils étaient connus.
6. Le statut d’un indicateur ne te donne pas, à lui seul, le motif exact de déclenchement ni la logique interne BeCLM. Tu ne dois pas inventer ce motif exact.
7. Tu es un compliance officer senior : pour chaque alerte, tu dois appliquer les meilleures pratiques de due diligence adaptées au cas, de façon proportionnée, traçable, opérationnelle et défendable.
8. Quand une information est absente, incohérente ou non exploitable, tu le signales clairement en écrivant à préciser ou non communiqué par BeCLM plutôt que d’extrapoler.
9. Tu n’inventes jamais de pays, de personnes, de faits, de flux, de documents, de valeurs cachées ou d’événements absents de la fiche.
10. Tu ne renommes jamais les indicateurs de la source 02.
11. Tu ne dois jamais traiter GAFI, UE, FR, Bale Institute et Cross border comme des synonymes.
12. La profondeur d’analyse, le niveau d’exigence, les mesures d’atténuation, les contrôles et les pièces demandées doivent être adaptés :
   - au statut de vigilance réel,
   - au niveau de risque global,
   - et au statut réel de chaque indicateur.
13. Tu dois proposer un dispositif basé sur la nature de l’alerte et sur les meilleures pratiques de conformité, jamais sur une valeur interne BeCLM supposée.

Exemples impératifs :
- Exemple Risque pays UE : si le pays exact, la contrepartie ou le flux précis ne sont pas explicitement fournis, ne nomme aucun pays et ne crée aucun scénario spécifique ; propose une diligence géographique générique au sens UE et écris pays concerné à préciser si nécessaire.
- Exemple SIREN / Catégorie juridique : si la forme juridique exacte ou la logique de classement BeCLM ne sont pas fournies, ne déduis pas la raison précise du déclenchement ; propose les diligences usuelles sur la structure, la gouvernance, la transparence et l’identification des parties prenantes.

Objectif :
Produire une analyse opérationnelle pour la revue du SIREN avec une sortie JSON structurée directement exploitable par l’application et par le PDF.

Règles d’analyse :
- Appuie-toi explicitement sur la fiche client complète.
- Analyse les vrais indicateurs de la source 02 présents dans `indicateurs_source_groupes`.
- Utilise exactement les noms des indicateurs fournis dans `indicateurs_source_groupes[].nom_indicateur`.
- Utilise `referentiel_indicateurs_actifs[].sens_metier` pour comprendre la signification métier des indicateurs, `regles_strictes` pour éviter les contresens et `cadre_methodologique_beclm` pour respecter les limites d’interprétation.
- Si un indicateur relève d’un classement interne ou référentiel BeCLM, dis-le explicitement.
- Quand une donnée métier précise manque, écris `à préciser` ou `non communiqué par BeCLM` et n’invente pas.
- Pour les indicateurs pays, distingue explicitement :
  - le classement GAFI,
  - la liste ou le référentiel UE,
  - le référentiel FR / paramétrage France,
  - l’indice Bale Institute,
  - et le caractère transfrontalier de Cross border.
- N’invente pas d’indicateur absent de la source 02.
- N’agrège pas plusieurs indicateurs dans un seul objet.
- Si un indicateur ne justifie pas d’action particulière, indique-le clairement de façon proportionnée.
- Si un indicateur appelle un renforcement, détaille précisément ce qui doit être contrôlé et quelles pièces sont attendues, en t’appuyant sur les meilleures pratiques de due diligence adaptées au cas.

Contenu attendu :
1. `explication_generale`
- Analyse globale du risque sur le SIREN.
- 2 lignes maximum.

2. `analyses_indicateurs`
- Une entrée par indicateur réel de la source 02 effectivement analysé.
- Pour chaque indicateur, renseigne obligatoirement :
  - `nom_indicateur`
  - `constat`
  - `niveau_attention`
  - `mesures_attenuation`
  - `controles_necessaires`
  - `pieces_a_demander`
- Les éléments doivent être concrets, opérationnels, directement exploitables par un analyste et alignés sur le sens métier BeCLM.
- Les recommandations doivent être fondées sur la nature de l’alerte et sur les meilleures pratiques de due diligence, pas sur un seuil ou une valeur interne supposés.

3. `conclusion_generale`
- Conclusion synthétique générale.
- Justifie le statut de vigilance estimé après remédiation.

4. `statut_estime`
- Tu peux proposer uniquement l’un des statuts suivants :
  - Aucune
  - Allégée
  - Modérée
  - Élevée
  - Critique

Format de sortie attendu :
Tu dois répondre exclusivement en JSON valide, sans texte avant ni après, avec la structure suivante :

{
  "explication_generale": "Analyse générale du risque sur le SIREN en 2 lignes maximum.",
  "analyses_indicateurs": [
    {
      "nom_indicateur": "Nom exact de l’indicateur de la source 02",
      "constat": "Constat factuel appuyé sur la fiche client, le sens métier BeCLM et les limites d’interprétation connues.",
      "niveau_attention": "Niveau d’attention ou de risque associé à l’indicateur.",
      "mesures_attenuation": "Mesures d’atténuation recommandées selon les meilleures pratiques de due diligence.",
      "controles_necessaires": "Contrôles nécessaires à réaliser selon les meilleures pratiques de conformité.",
      "pieces_a_demander": "Pièces justificatives ou documents à demander sans supposer une logique interne BeCLM non fournie."
    }
  ],
  "conclusion_generale": "Conclusion synthétique générale et justification du statut estimé.",
  "statut_estime": "Aucune | Allégée | Modérée | Élevée | Critique"
}"""


    st.markdown(
        """
        <style>
        div[data-testid="stVerticalBlock"]:has(#agent-ia-config-anchor) {
            margin: 0.2rem 0 0.95rem 0;
            padding: 1rem 1.05rem 1rem 1.05rem;
            border-radius: 22px;
            border: 1px solid rgba(22, 58, 89, 0.14);
            background: linear-gradient(180deg, rgba(230, 238, 247, 0.92), rgba(242, 247, 253, 0.88));
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.72), 0 4px 14px rgba(22,58,89,0.04);
        }
        div[data-testid="stVerticalBlock"]:has(#agent-ia-config-anchor) > div[data-testid="stHorizontalBlock"] {
            margin-top: 0.25rem;
        }
        div[data-testid="stVerticalBlock"]:has(#agent-ia-config-anchor) p {
            margin-bottom: 0;
        }
        .agent-ia-card-kicker {
            font-family: 'Sora', sans-serif;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #2F6B9E;
            margin-bottom: 0.12rem;
        }
        .agent-ia-card-title {
            font-family: 'Montserrat', sans-serif;
            font-size: 1.05rem;
            font-weight: 800;
            color: var(--cm-primary);
            margin-bottom: 0.18rem;
        }
        .agent-ia-card-note {
            font-size: 0.92rem;
            line-height: 1.42;
            color: var(--cm-muted);
            margin-bottom: 0.55rem;
        }
        .agent-ia-field-label {
            font-size: 0.9rem;
            font-weight: 700;
            color: var(--cm-primary);
            line-height: 1.15;
            min-height: 1.15rem;
            margin: 0 0 0.32rem 0;
        }
        div[data-testid="stVerticalBlock"]:has(#agent-ia-config-anchor) div[data-testid="stTextInputRootElement"] > div,
        div[data-testid="stVerticalBlock"]:has(#agent-ia-config-anchor) div[data-baseweb="base-input"] > div,
        div[data-testid="stVerticalBlock"]:has(#agent-ia-config-anchor) div[data-testid="stTextArea"] div[data-baseweb="textarea"] {
            border-radius: 14px !important;
            border: 1px solid rgba(47, 107, 158, 0.22) !important;
            background: #FFFFFF !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.88), 0 1px 3px rgba(22,58,89,0.04) !important;
        }
        div[data-testid="stVerticalBlock"]:has(#agent-ia-config-anchor) div[data-baseweb="base-input"] > div {
            min-height: 2.85rem !important;
        }
        div[data-testid="stVerticalBlock"]:has(#agent-ia-config-anchor) div[data-testid="stTextInputRootElement"] input {
            font-size: 0.96rem !important;
            line-height: 1.35 !important;
            color: var(--cm-primary) !important;
            background: transparent !important;
        }
        div[data-testid="stVerticalBlock"]:has(#agent-ia-config-anchor) div[data-testid="stTextArea"] {
            width: 100% !important;
            margin: 0 !important;
        }
        div[data-testid="stVerticalBlock"]:has(#agent-ia-config-anchor) div[data-testid="stTextArea"] label {
            margin: 0 !important;
            min-height: 0 !important;
        }
        div[data-testid="stVerticalBlock"]:has(#agent-ia-config-anchor) div[data-testid="stTextArea"] div[data-baseweb="base-input"] {
            min-height: 10rem !important;
            height: auto !important;
            align-items: stretch !important;
            background: #FFFFFF !important;
            overflow: visible !important;
        }
        div[data-testid="stVerticalBlock"]:has(#agent-ia-config-anchor) div[data-testid="stTextArea"] div[data-baseweb="textarea"] {
            min-height: 10rem !important;
            height: auto !important;
            background: #FFFFFF !important;
            box-sizing: border-box !important;
            overflow: visible !important;
        }
        div[data-testid="stVerticalBlock"]:has(#agent-ia-config-anchor) textarea[aria-label="Prompt Agent IA"] {
            font-size: 0.96rem !important;
            line-height: 1.35 !important;
            color: var(--cm-primary) !important;
            background: #FFFFFF !important;
            min-height: 10rem !important;
            box-sizing: border-box !important;
            resize: vertical !important;
            overflow: auto !important;
            padding: 0.62rem 0.95rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container():
        st.markdown(
            """
            <div id="agent-ia-config-anchor"></div>
            <div class="agent-ia-card-kicker">Agent IA</div>
            <div class="agent-ia-card-title">Pilotez vos revues avec les analyses de l’agent IA BeCLM</div>
            <div class="agent-ia-card-note">Renseignez la clé de l’agent et ajustez le prompt pour lancer les analyses IA et alimenter la colonne Explique moi.</div>
            """,
            unsafe_allow_html=True,
        )
        prompt_state_key = "review_sim_show_prompt"
        prompt_value_key = "review_sim_prompt_preview"
        prompt_version_key = "review_sim_prompt_preview_version"
        current_prompt_value = st.session_state.get(prompt_value_key)
        prompt_version = str(st.session_state.get(prompt_version_key, "") or "").strip()
        prompt_needs_refresh = (
            not isinstance(current_prompt_value, str)
            or not current_prompt_value.strip()
            or (prompt_version != "v216" and "Les valeurs détaillées des indicateurs, les seuils de déclenchement" not in str(current_prompt_value))
        )
        if prompt_needs_refresh:
            st.session_state[prompt_value_key] = default_prompt
        st.session_state[prompt_version_key] = "v216"
        control_col, action_col = st.columns([1, 1], gap="medium")
        with control_col:
            st.markdown('<div class="agent-ia-field-label">Clé Agent IA</div>', unsafe_allow_html=True)
            gemini_api_key = st.text_input(
                "Clé Agent IA",
                type="password",
                key=REVIEW_SIM_GEMINI_KEY_STATE,
                placeholder="AIza...",
                help="Clé éphémère : elle n’est pas sauvegardée et est effacée lorsque vous changez d’écran ou fermez l’application.",
                label_visibility="collapsed",
            ).strip()
        with action_col:
            st.markdown('<div class="agent-ia-field-label">Prompt Agent IA</div>', unsafe_allow_html=True)
            prompt_is_visible = bool(st.session_state.get(prompt_state_key, False))
            if st.button(
                "Masquer le prompt" if prompt_is_visible else "Afficher le prompt",
                key="review_sim_toggle_prompt_visibility",
                use_container_width=True,
                type="secondary",
            ):
                prompt_is_visible = not prompt_is_visible
                st.session_state[prompt_state_key] = prompt_is_visible
            else:
                prompt_is_visible = bool(st.session_state.get(prompt_state_key, False))
        if prompt_is_visible:
            st.markdown("<div style='height: 0.45rem;'></div>", unsafe_allow_html=True)
            st.markdown('<div class="agent-ia-field-label">Prompt Agent IA</div>', unsafe_allow_html=True)
            st.text_area(
                "Prompt Agent IA",
                height=160,
                key=prompt_value_key,
                help="Prompt standard modifiable pour l’analyse IA.",
                label_visibility="collapsed",
            )
        base_prompt = str(st.session_state.get(prompt_value_key, default_prompt)).strip() or default_prompt

    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

    search_catalog = (
        base_df[["SIREN", "Dénomination"]]
        .copy()
        .assign(
            SIREN=lambda df: df["SIREN"].astype(str).str.strip(),
            Dénomination=lambda df: df["Dénomination"].fillna("").astype(str).str.strip(),
        )
        .drop_duplicates(subset=["SIREN"])
        .sort_values(["Dénomination", "SIREN"], kind="stable")
    )
    search_options: list[tuple[str, str]] = [("", "")] + [
        (row["SIREN"], row["Dénomination"]) for _, row in search_catalog.iterrows()
    ]

    search_choice = st.selectbox(
        "Rechercher un SIREN ou une dénomination",
        options=search_options,
        index=0,
        format_func=lambda item: (
            "Tous les SIREN / dénominations"
            if not item[0]
            else f"{item[0]} — {item[1]}" if item[1] else item[0]
        ),
        key="review_sim_search_choice",
        help="Commencez à saisir un SIREN ou une dénomination puis choisissez une ligne dans la liste.",
    )

    working_df = base_df.copy()
    if search_choice and search_choice[0]:
        selected_siren = str(search_choice[0]).strip()
        working_df = working_df[working_df["SIREN"].astype(str).str.strip() == selected_siren].copy()

    if working_df.empty:
        st.info("Aucun SIREN ne correspond au critère de recherche retenu.")
        return

    render_review_status_gauges(working_df)

    status_filter_options = list(VIGILANCE_ORDER)
    default_real_filter = st.session_state.get("review_sim_real_filter")
    if not isinstance(default_real_filter, list) or not default_real_filter:
        default_real_filter = list(status_filter_options)

    st.markdown(
        """
        <style>
        .stMultiSelect [data-baseweb="tag"] {
            background: #F5F7FA !important;
            border: 1px solid rgba(22, 58, 89, 0.16) !important;
            border-radius: 999px !important;
            box-shadow: none !important;
        }
        .stMultiSelect [data-baseweb="tag"]:hover {
            background: #EEF2F6 !important;
            border-color: rgba(22, 58, 89, 0.20) !important;
        }
        .stMultiSelect [data-baseweb="tag"] *,
        .stMultiSelect [data-baseweb="tag"] span,
        .stMultiSelect [data-baseweb="tag"] div,
        .stMultiSelect [data-baseweb="tag"] p {
            background: transparent !important;
            color: #163A59 !important;
            fill: #163A59 !important;
            font-family: "Source Sans Pro", sans-serif !important;
        }
        .stMultiSelect [data-baseweb="tag"] svg {
            color: #5B7084 !important;
            fill: #5B7084 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    current_filter = st.multiselect(
        "Filtrer sur le statut de vigilance réel",
        options=status_filter_options,
        default=[v for v in default_real_filter if v in status_filter_options] or list(status_filter_options),
        format_func=format_review_simulation_vigilance_filter_option,
        key="review_sim_real_filter",
        help="Ce filtre agit sur le tableau Revues & Simulations.",
    )
    if current_filter:
        working_df = working_df[working_df[REVIEW_SIM_REAL_LABEL].astype(str).isin(current_filter)].copy()
    else:
        working_df = working_df.iloc[0:0].copy()

    working_df = working_df.reset_index(drop=True)

    if working_df.empty:
        st.info("Aucun SIREN ne correspond au filtre de statut de vigilance retenu.")
        return

    selected_keys = st.session_state.get("review_sim_selected_keys", [])
    if not isinstance(selected_keys, list):
        selected_keys = []
        st.session_state["review_sim_selected_keys"] = []

    selected_rows = review_sim_rows_from_selection(working_df, selected_keys)
    selected_count = len(selected_rows)
    selected_df = working_df.iloc[selected_rows].copy() if selected_rows else working_df.iloc[0:0].copy()
    selected_pdf_items = review_simulation_available_pdfs(working_df, selected_rows)
    zip_pdf_items = review_simulation_available_pdfs(base_df)

    status_options = list(VIGILANCE_ORDER)
    default_value = "Vigilance Modérée"
    if selected_rows:
        current_values = working_df.iloc[selected_rows][REVIEW_SIM_EST_LABEL].astype(str).dropna().unique().tolist()
        if len(current_values) == 1 and current_values[0] in status_options:
            default_value = current_values[0]
        else:
            first_value = str(working_df.iloc[selected_rows[0]][REVIEW_SIM_EST_LABEL]).strip()
            if first_value in status_options:
                default_value = first_value

    status_display_map = {
        "Vigilance Critique": "Critique",
        "Vigilance Élevée": "Élevée",
        "Vigilance Modérée": "Modérée",
        "Vigilance Allégée": "Allégée",
        "Vigilance Aucune": "Aucune",
    }
    csv_export_bytes = dataframe_to_csv_bytes(build_review_simulation_export_dataframe(working_df))
    single_pdf_bytes: bytes | None = None
    single_pdf_name = "revue_simulation.pdf"
    single_pdf_mime = "application/pdf"
    if REPORTLAB_AVAILABLE and selected_count == 1 and selected_pdf_items:
        single_pdf_bytes, single_pdf_name, single_pdf_mime = review_simulation_single_download_payload(selected_pdf_items)
    zip_pdf_bytes = review_simulation_pdfs_zip_bytes(zip_pdf_items) if REPORTLAB_AVAILABLE and zip_pdf_items else None
    gemini_button_disabled = (selected_count == 0) or (not gemini_api_key)

    inject_review_sim_toolbar_style()
    toolbar_cols = st.columns([1.15, 1.95, 1.15, 1.15, 0.90, 1.10, 0.70], gap="small")

    clear_clicked = False
    apply_clicked = False
    gemini_clicked = False

    with toolbar_cols[0]:
        st.markdown("<div style='height: 1.9rem;'></div>", unsafe_allow_html=True)
        clear_clicked = st.button(
            "Effacer",
            key="review_toolbar_clear",
            type="secondary",
            disabled=(selected_count == 0),
            use_container_width=True,
            help="Vide la sélection mémorisée du tableau des sociétés.",
        )
    with toolbar_cols[1]:
        manual_status = st.selectbox(
            "Statut estimé",
            options=status_options,
            index=status_options.index(default_value),
            key="review_sim_manual_status",
            disabled=(selected_count == 0),
            format_func=lambda value: status_display_map.get(value, str(value).replace("Vigilance ", "")),
            help="Choisissez le statut estimé à appliquer à toutes les lignes sélectionnées.",
        )
    with toolbar_cols[2]:
        st.markdown("<div style='height: 1.9rem;'></div>", unsafe_allow_html=True)
        apply_clicked = st.button(
            "Appliquer",
            key="review_toolbar_apply",
            type="primary",
            disabled=(selected_count == 0),
            use_container_width=True,
            help="Met à jour le statut estimé des sociétés sélectionnées.",
        )
    with toolbar_cols[3]:
        st.markdown("<div style='height: 1.9rem;'></div>", unsafe_allow_html=True)
        gemini_clicked = st.button(
            "Agent IA",
            key="review_toolbar_gemini",
            type="secondary",
            disabled=gemini_button_disabled,
            use_container_width=True,
            help=f"Analyse la sélection courante avec Gemini (maximum {GEMINI_MAX_BATCH_SIZE} SIREN envoyés).",
        )
    with toolbar_cols[4]:
        st.markdown("<div style='height: 1.9rem;'></div>", unsafe_allow_html=True)
        review_simulation_download_button(
            "PDF(s)",
            data=(single_pdf_bytes or b""),
            file_name=single_pdf_name,
            mime=single_pdf_mime,
            key="review_toolbar_pdf",
            disabled=(single_pdf_bytes is None),
            use_container_width=True,
            help="Télécharge le PDF du SIREN sélectionné, ou un ZIP lorsque plusieurs documents PDF existent pour le dossier.",
        )
    with toolbar_cols[5]:
        st.markdown("<div style='height: 1.9rem;'></div>", unsafe_allow_html=True)
        review_simulation_download_button(
            "ZIP PDF",
            data=(zip_pdf_bytes or b""),
            file_name="revues_simulations_tous_pdfs.zip",
            mime="application/zip",
            key="review_toolbar_zip_pdf",
            disabled=(zip_pdf_bytes is None),
            use_container_width=True,
            help="Télécharge tous les PDF structurés déjà générés sur le périmètre courant dans un fichier ZIP.",
        )
    with toolbar_cols[6]:
        st.markdown("<div style='height: 1.9rem;'></div>", unsafe_allow_html=True)
        review_simulation_download_button(
            "CSV",
            data=csv_export_bytes,
            file_name="revues_et_simulations.csv",
            mime="text/csv;charset=utf-8",
            key="review_toolbar_csv",
            use_container_width=True,
            help="Exporte le tableau Revues & Simulations visible, y compris la colonne « Explique moi ».",
        )

    if clear_clicked:
        st.session_state["review_sim_selected_keys"] = []
        st.session_state["review_sim_table_version"] = int(st.session_state.get("review_sim_table_version", 0)) + 1
        selected_keys = []
        selected_rows = []
        selected_count = 0
        selected_df = working_df.iloc[0:0].copy()

    if apply_clicked and selected_rows:
        updated_df, updated_count = apply_manual_estimated_status(working_df, selected_rows, manual_status)
        working_df = updated_df.reset_index(drop=True)
        pdf_count, pdf_errors = persist_review_simulation_subset(working_df, selected_rows)
        notice = f"{updated_count} SIREN mis à jour avec le statut estimé « {manual_status} »."
        if pdf_count:
            notice += f" {pdf_count} PDF structuré(s) généré(s) ou mis à jour."
        st.session_state["review_sim_notice"] = notice
        if pdf_errors:
            st.session_state["review_sim_warning"] = " | ".join(pdf_errors[:3])

    if gemini_clicked and selected_rows:
        base_source_df, indicators_source_df, _ = load_source_data()
        source_df = build_review_simulation_source_dataset(portfolio, base_source_df, indicators_source_df)
        with st.spinner("Analyse Gemini en cours sur les lignes sélectionnées…"):
            updated_df, processed, errors = apply_gemini_review_simulation_batch(
                working_df,
                selected_rows,
                source_df,
                api_key=gemini_api_key,
                base_prompt=base_prompt,
                model=GEMINI_MODEL_DEFAULT,
            )
        working_df = updated_df.reset_index(drop=True)
        pdf_count, pdf_errors = persist_review_simulation_subset(
            working_df,
            selected_rows[:GEMINI_MAX_BATCH_SIZE],
            pdf_source_df=source_df,
            prompt_template=base_prompt,
        )
        combined_errors = list(errors)
        combined_errors.extend(pdf_errors)
        if processed == 0:
            st.session_state["review_sim_warning"] = combined_errors[0] if combined_errors else "Sélectionnez au moins un SIREN pour lancer Gemini."
        else:
            if selected_count > GEMINI_MAX_BATCH_SIZE:
                notice = f"{processed} SIREN traités par Gemini. Seuls les {GEMINI_MAX_BATCH_SIZE} premiers SIREN sélectionnés ont été envoyés."
            else:
                notice = f"{processed} SIREN traités par Gemini dans le lot courant."
            if pdf_count:
                notice += f" {pdf_count} PDF structuré(s) généré(s) ou mis à jour."
            st.session_state["review_sim_notice"] = notice
            if combined_errors:
                preview_errors = " | ".join(combined_errors[:3])
                if len(combined_errors) > 3:
                    preview_errors += f" | +{len(combined_errors) - 3} autre(s) erreur(s)"
                st.session_state["review_sim_warning"] = preview_errors

    if clear_clicked or apply_clicked or gemini_clicked:
        selected_keys = st.session_state.get("review_sim_selected_keys", []) if not clear_clicked else []
        if not isinstance(selected_keys, list):
            selected_keys = []
        selected_rows = review_sim_rows_from_selection(working_df, selected_keys)

    table_version = int(st.session_state.get("review_sim_table_version", 0))
    table_selected_rows = render_review_simulation_table(working_df, key=f"review_sim_table_{table_version}")

    if table_selected_rows:
        st.session_state["review_sim_selected_keys"] = review_sim_selection_keys(working_df, table_selected_rows)
    elif "review_sim_selected_keys" not in st.session_state:
        st.session_state["review_sim_selected_keys"] = []

    if not REPORTLAB_AVAILABLE:
        st.info(PDF_DEPENDENCY_ERROR_MESSAGE)

    review_simulation_emit_feedback()

    render_review_simulation_indicator_reference_expander()
    render_review_simulation_glossary_expander()

    render_review_simulation_explain_overlay(working_df)



def build_dataset_cache_signature() -> str:
    manifest = load_manifest() or {}
    current_dir = active_dataset_path()
    parts = [PORTFOLIO_PIPELINE_VERSION, str(manifest.get("published_at_utc", ""))]
    for filename in DATA_FILES.values():
        path = current_dir / filename
        if path.exists():
            stat = path.stat()
            parts.append(f"{filename}:{stat.st_mtime_ns}:{stat.st_size}")
        else:
            parts.append(f"{filename}:missing")
    return "|".join(parts)


@st.cache_data(show_spinner=False)
def get_app_datasets_cached(signature: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base = load_source_data()
    portfolio = build_portfolio_dataset()
    return base[0], base[1], base[2], portfolio


def load_app_datasets() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    signature = build_dataset_cache_signature()
    base, indicators, history, portfolio = get_app_datasets_cached(signature)
    return base.copy(), indicators.copy(), history.copy(), portfolio.copy()


def load_source_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    current_dir = active_dataset_path()
    if not current_dir.exists():
        raise NoPublishedDatasetError(
            "Aucun jeu de données publié. Connectez-vous avec un compte admin puis chargez les 3 fichiers CSV depuis la barre latérale."
        )

    def _read(label: str) -> pd.DataFrame:
        path = current_dir / DATA_FILES[label]
        if not path.exists():
            raise NoPublishedDatasetError(
                "Jeu de données incomplet côté serveur. Republiez les 3 fichiers 01, 02 et 03 depuis un compte admin."
            )
        return read_csv_semicolon(path)

    base = _read("base")
    indicators = _read("indicators")
    history = _read("history")

    validate_required_columns(base, "base")
    validate_required_columns(indicators, "indicators")
    validate_required_columns(history, "history")

    for df in (base, indicators, history):
        df[SOC_COL] = normalize_societe_id(df[SOC_COL])
        df["SIREN"] = normalize_siren(df["SIREN"])
        df.dropna(subset=KEY_COLUMNS, inplace=True)

    base = base.drop_duplicates(subset=KEY_COLUMNS, keep="first").copy()
    indicators = indicators.drop_duplicates(subset=KEY_COLUMNS, keep="first").copy()

    for col in [
        "Cross border",
        "Cash intensité",
        "Part des opérations à distance 12 mois",
        "Part des opérations avec produits(services) hauts risques 12 mois",
    ]:
        if col in base.columns:
            base[col] = base[col].apply(parse_percent)

    for col in ["Date dernière revue", "Date prochaine revue"]:
        if col in base.columns:
            base[col] = pd.to_datetime(base[col], errors="coerce", dayfirst=True)

    for col in indicators.columns:
        if "Date de mise à jour" in col:
            indicators[col] = pd.to_datetime(indicators[col], errors="coerce", dayfirst=True)

    for frame, columns in [
        (
            base,
            [
                "Dénomination",
                "Pays de résidence",
                "Segment",
                "Produit(service) principal",
                "Canal d’opérations principal 12 mois",
                "Statut EDD",
                "Flag justificatif complet",
                "Analyste",
                "Valideur",
                BASE_RISK_SOURCE_COLUMN,
            ],
        ),
        (indicators, ["Vigilance statut", "Cash intensité Statut"]),
    ]:
        for col in columns:
            if col in frame.columns:
                frame[col] = clean_text_column(frame[col])

    if BASE_RISK_SOURCE_COLUMN in base.columns:
        base[BASE_RISK_SOURCE_COLUMN] = (
            base[BASE_RISK_SOURCE_COLUMN]
            .apply(canonical_risk_label)
            .replace({"": pd.NA})
            .astype("string")
        )

    if "Vigilance statut" in indicators.columns:
        indicators["Vigilance statut"] = (
            indicators["Vigilance statut"]
            .apply(canonical_vigilance_label)
            .replace({"": pd.NA})
            .astype("string")
        )

    for col in indicator_status_columns(indicators):
        if col in indicators.columns:
            indicators[col] = clean_text_column(indicators[col])

    return base, indicators, history


def indicator_status_columns(indicators_df: pd.DataFrame) -> list[str]:
    cols = [c for c in indicators_df.columns if re.search(r"(?i)\bstatut\b", c)]
    return [c for c in cols if c != "Vigilance statut"]


def indicator_risk_breakdown_columns(indicators_df: pd.DataFrame) -> list[str]:
    excluded = {"Cash intensité Statut", BASE_RISK_SOURCE_COLUMN}
    return [c for c in indicator_status_columns(indicators_df) if c not in excluded]


def build_indicator_status_occurrence_counts(indicators_df: pd.DataFrame) -> pd.DataFrame:
    empty = (
        indicators_df[KEY_COLUMNS].copy()
        if indicators_df is not None and all(col in indicators_df.columns for col in KEY_COLUMNS)
        else pd.DataFrame(columns=KEY_COLUMNS)
    )
    for column_name in STATUS_COUNT_COLUMNS:
        empty[column_name] = 0

    if indicators_df is None or indicators_df.empty or not all(col in indicators_df.columns for col in KEY_COLUMNS):
        return empty

    counts = indicators_df[KEY_COLUMNS].copy()

    risk_scan_columns = [col for col in indicator_status_columns(indicators_df) if col in indicators_df.columns]
    vigilance_scan_columns = [
        col
        for col in dict.fromkeys(["Vigilance statut", *risk_scan_columns])
        if col in indicators_df.columns
    ]

    if vigilance_scan_columns:
        vigilance_statuses = indicators_df[vigilance_scan_columns].apply(
            lambda series: series.map(canonical_vigilance_label)
        )
        for label in VIGILANCE_ORDER:
            counts[f"Nb {label}"] = vigilance_statuses.eq(label).sum(axis=1).astype(int)
    else:
        for label in VIGILANCE_ORDER:
            counts[f"Nb {label}"] = 0

    if risk_scan_columns:
        risk_statuses = indicators_df[risk_scan_columns].apply(
            lambda series: series.map(canonical_risk_label)
        )
        for label in RISK_ORDER:
            counts[f"Nb {label}"] = risk_statuses.eq(label).sum(axis=1).astype(int)
    else:
        for label in RISK_ORDER:
            counts[f"Nb {label}"] = 0

    numeric_cols = [col for col in counts.columns if col not in KEY_COLUMNS]
    if numeric_cols:
        counts = counts.groupby(KEY_COLUMNS, as_index=False)[numeric_cols].sum()
    return counts


def build_risk_alert_distribution(df: pd.DataFrame) -> pd.DataFrame:
    empty = pd.DataFrame([{"Libellé": label, "Nb": 0, "%": 0.0} for label in RISK_ORDER])
    if df is None or df.empty:
        return empty

    client_level = build_unique_client_snapshot(df, RISK_COUNT_COLUMNS)
    if client_level.empty:
        return empty

    total = int(client_level[RISK_COUNT_COLUMNS].apply(pd.to_numeric, errors="coerce").fillna(0).to_numpy().sum()) if all(col in client_level.columns for col in RISK_COUNT_COLUMNS) else 0
    rows = []
    for label in RISK_ORDER:
        column_name = f"Nb {label}"
        nb = int(pd.to_numeric(client_level.get(column_name, 0), errors="coerce").fillna(0).sum())
        rows.append({"Libellé": label, "Nb": nb, "%": (nb / total if total else 0.0)})
    return pd.DataFrame(rows)


def build_portfolio_dataset() -> pd.DataFrame:
    base, indicators, history = load_source_data()

    status_occurrence_counts = build_indicator_status_occurrence_counts(indicators)
    indicator_cols = [
        SOC_COL,
        "SIREN",
        "Vigilance statut",
        "Vigilance valeur",
        "Vigilance Date de mise à jour",
        "Cash intensité Statut",
    ]
    indicator_cols = list(dict.fromkeys([c for c in indicator_cols if c in indicators.columns]))

    portfolio = base.merge(indicators[indicator_cols], how="left", on=KEY_COLUMNS)
    portfolio = portfolio.merge(status_occurrence_counts, how="left", on=KEY_COLUMNS)
    history_count = history.groupby(KEY_COLUMNS).size().rename("Nb historique").reset_index()
    portfolio = portfolio.merge(history_count, how="left", on=KEY_COLUMNS)
    portfolio["Nb historique"] = portfolio["Nb historique"].fillna(0).astype(int)

    portfolio["Vigilance"] = portfolio.get("Vigilance statut")
    portfolio["Risque"] = portfolio.get(BASE_RISK_SOURCE_COLUMN, pd.Series(index=portfolio.index, dtype="string"))

    for column_name in STATUS_COUNT_COLUMNS:
        portfolio[column_name] = pd.to_numeric(portfolio.get(column_name, 0), errors="coerce").fillna(0).astype(int)

    today = pd.Timestamp.today().normalize()
    portfolio["Alerte justificatif incomplet"] = (
        (portfolio.get("Flag justificatif complet") != "Oui")
        & (portfolio["Vigilance"].isin(CRITICAL_VIGILANCE))
    ).astype(int)
    portfolio["Alerte vigilance critique"] = (portfolio["Vigilance"] == "Vigilance Critique").astype(int)
    portfolio["Alerte revue trop ancienne"] = (
        portfolio["Vigilance"].isin(CRITICAL_VIGILANCE)
        & portfolio.get("Date dernière revue", pd.Series(index=portfolio.index, dtype="datetime64[ns]")).notna()
        & ((today - portfolio["Date dernière revue"]).dt.days > 90)
    ).astype(int)
    portfolio["Alerte sans prochaine revue"] = portfolio.get(
        "Date prochaine revue", pd.Series(index=portfolio.index, dtype="datetime64[ns]")
    ).isna().astype(int)
    portfolio["Alerte cross-border élevé"] = portfolio.get(
        "Cross border", pd.Series(index=portfolio.index, dtype="float64")
    ).ge(0.25).fillna(False).astype(int)
    portfolio["Alerte cash intensité élevée"] = (
        portfolio.get("Cash intensité Statut", pd.Series(index=portfolio.index, dtype="string"))
        .isin(PRIORITY_RISK)
        .astype(int)
    )

    portfolio["Score priorité"] = (
        25 * (portfolio["Vigilance"] == "Vigilance Critique").astype(int)
        + 15 * (portfolio["Vigilance"] == "Vigilance Élevée").astype(int)
        + 20 * (portfolio["Risque"] == "Risque avéré").astype(int)
        + 10 * (portfolio["Risque"] == "Risque potentiel").astype(int)
        + 12 * portfolio["Alerte justificatif incomplet"]
        + 8 * portfolio["Alerte vigilance critique"]
        + 6 * portfolio["Alerte revue trop ancienne"]
        + 8 * portfolio["Alerte sans prochaine revue"]
        + 5 * portfolio["Alerte cross-border élevé"]
    )

    motifs = (
        np.where(portfolio["Alerte justificatif incomplet"].eq(1), "Justificatif incomplet ", "")
        + np.where(portfolio["Alerte vigilance critique"].eq(1), "Vigilance critique ", "")
        + np.where(portfolio["Alerte revue trop ancienne"].eq(1), "Revue trop ancienne ", "")
        + np.where(portfolio["Alerte sans prochaine revue"].eq(1), "Sans prochaine revue ", "")
        + np.where(portfolio["Alerte cross-border élevé"].eq(1), "Cross-border élevé ", "")
    )
    portfolio["Motifs"] = pd.Series(motifs, index=portfolio.index, dtype="string").str.strip()
    return portfolio


def non_empty_sorted(values) -> list[str]:
    return sorted({str(v).strip() for v in values if pd.notna(v) and str(v).strip()})


def available_societies(df: pd.DataFrame) -> list[str]:
    if SOC_COL not in df.columns:
        return []
    return non_empty_sorted(df[SOC_COL].unique())


def restrict_to_societies(df: pd.DataFrame, societies: list[str]) -> pd.DataFrame:
    normalized = {str(s).strip().upper() for s in societies if str(s).strip()}
    if not normalized:
        return df.iloc[0:0].copy()
    return df[df[SOC_COL].astype(str).str.upper().isin(normalized)].copy()


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    result = df.copy()
    for label, value in filters.items():
        if value == "Tous":
            continue
        result = result[result[FILTER_MAPPING[label]] == value]
    return result


def build_unique_client_snapshot(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    if df is None or df.empty:
        if columns:
            return pd.DataFrame(columns=columns)
        return df.iloc[0:0].copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()

    work = df.copy()
    if SOC_COL in work.columns and "SIREN" in work.columns:
        work["cm_client_key"] = work[SOC_COL].astype(str).str.strip() + "|" + work["SIREN"].astype(str).str.strip()
    elif "SIREN" in work.columns:
        work["cm_client_key"] = work["SIREN"].astype(str).str.strip()
    else:
        work["cm_client_key"] = pd.Series(range(len(work)), index=work.index).astype(str)

    if columns:
        keep_columns = [col for col in columns if col in work.columns]
        if "cm_client_key" not in keep_columns:
            keep_columns.insert(0, "cm_client_key")
        work = work[keep_columns]

    return work.drop_duplicates(subset=["cm_client_key"], keep="first").reset_index(drop=True)


def build_distribution(df: pd.DataFrame, column: str, order: list[str]) -> pd.DataFrame:
    client_level = build_unique_client_snapshot(df, [column])
    if column not in client_level.columns:
        return pd.DataFrame([{"Libellé": item, "Nb": 0, "%": 0.0} for item in order])

    counts = client_level[column].value_counts(dropna=False)
    total = len(client_level)
    rows = []
    for item in order:
        nb = int(counts.get(item, 0))
        rows.append({"Libellé": item, "Nb": nb, "%": (nb / total if total else 0.0)})
    return pd.DataFrame(rows)


def build_alert_table(df: pd.DataFrame) -> pd.DataFrame:
    alert_columns = [
        "Alerte justificatif incomplet",
        "Alerte vigilance critique",
        "Alerte revue trop ancienne",
        "Alerte sans prochaine revue",
        "Alerte cross-border élevé",
        "Alerte cash intensité élevée",
    ]
    client_level = build_unique_client_snapshot(df, alert_columns)
    rows = [
        ("Justificatif incomplet", int(client_level.get("Alerte justificatif incomplet", pd.Series(0, index=client_level.index)).fillna(0).sum())),
        ("Vigilance critique", int(client_level.get("Alerte vigilance critique", pd.Series(0, index=client_level.index)).fillna(0).sum())),
        ("Revue trop ancienne", int(client_level.get("Alerte revue trop ancienne", pd.Series(0, index=client_level.index)).fillna(0).sum())),
        ("Sans prochaine revue", int(client_level.get("Alerte sans prochaine revue", pd.Series(0, index=client_level.index)).fillna(0).sum())),
        ("Cross-border élevé", int(client_level.get("Alerte cross-border élevé", pd.Series(0, index=client_level.index)).fillna(0).sum())),
        ("Cash intensité élevée", int(client_level.get("Alerte cash intensité élevée", pd.Series(0, index=client_level.index)).fillna(0).sum())),
    ]
    return pd.DataFrame(rows, columns=["Alerte", "Nb"])


CONCENTRATION_VIGILANCE_PERCENT_COLUMNS = [
    ("Vigilance Critique", "% Vig. crit."),
    ("Vigilance Élevée", "% Vig. élev."),
    ("Vigilance Modérée", "% Vig. mod."),
    ("Vigilance Allégée", "% Vig. all."),
    ("Vigilance Aucune", "% Vig. auc."),
]

CONCENTRATION_RISK_PERCENT_COLUMNS = [
    ("Risque avéré", "% Risq. av."),
    ("Risque potentiel", "% Risq. pot."),
    ("Risque mitigé", "% Risq. mit."),
    ("Risque levé", "% Risq. lev."),
    ("Non calculable", "% Risq. NC"),
    ("Aucun risque détecté", "% Risq. aucun"),
]

CONCENTRATION_SORT_OPTIONS = ["% clients", "% vigilance", "% risque"]
CONCENTRATION_VIGILANCE_SORT_PRIORITY = [
    "% Vig. crit.",
    "% Vig. élev.",
    "% Vig. mod.",
    "% Vig. all.",
    "% Vig. auc.",
]
CONCENTRATION_RISK_SORT_PRIORITY = [
    "% Risq. av.",
    "% Risq. pot.",
    "% Risq. NC",
    "% Risq. mit.",
    "% Risq. lev.",
    "% Risq. aucun",
]

CONCENTRATION_STATUS_STYLE = {
    "% Vig. crit.": {"tone": "negative", "base": "#D92D20", "text": "#7A271A"},
    "% Vig. élev.": {"tone": "negative", "base": "#F79009", "text": "#8A4B00"},
    "% Vig. mod.": {"tone": "neutral", "base": "#FACC15", "text": "#713F12"},
    "% Vig. all.": {"tone": "positive", "base": "#16A34A", "text": "#14532D"},
    "% Vig. auc.": {"tone": "positive", "base": "#16A34A", "text": "#14532D"},
    "% Risq. av.": {"tone": "negative", "base": "#D92D20", "text": "#7A271A"},
    "% Risq. pot.": {"tone": "negative", "base": "#F79009", "text": "#8A4B00"},
    "% Risq. mit.": {"tone": "positive", "base": "#22C55E", "text": "#166534"},
    "% Risq. lev.": {"tone": "positive", "base": "#16A34A", "text": "#14532D"},
    "% Risq. NC": {"tone": "neutral", "base": "#94A3B8", "text": "#475569"},
    "% Risq. aucun": {"tone": "positive", "base": "#16A34A", "text": "#14532D"},
}


def sort_concentration_top_table(df: pd.DataFrame, group_label: str, sort_mode: str) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    sort_value = str(sort_mode or "% clients").strip().lower()
    if sort_value == "% vigilance":
        sort_columns = [col for col in CONCENTRATION_VIGILANCE_SORT_PRIORITY if col in df.columns]
        ascending = [False] * len(sort_columns)
    elif sort_value == "% risque":
        sort_columns = [col for col in CONCENTRATION_RISK_SORT_PRIORITY if col in df.columns]
        ascending = [False] * len(sort_columns)
    else:
        sort_columns = ["% clients"]
        ascending = [False]

    for column_name, is_ascending in [("Nb clients", False), (group_label, True)]:
        if column_name in df.columns:
            sort_columns.append(column_name)
            ascending.append(is_ascending)

    return df.sort_values(sort_columns, ascending=ascending, kind="stable").reset_index(drop=True)


def build_concentration_top_table(
    df: pd.DataFrame,
    group_col: str,
    group_label: str,
    top_n: int = 5,
    sort_mode: str = "% clients",
) -> pd.DataFrame:
    percent_columns = CONCENTRATION_VIGILANCE_PERCENT_COLUMNS + CONCENTRATION_RISK_PERCENT_COLUMNS
    output_columns = [group_label, "Nb clients", "% clients"] + [column_name for _, column_name in percent_columns]

    if group_col not in df.columns:
        return pd.DataFrame(columns=output_columns)

    work = df.copy()
    work[group_col] = (
        work[group_col]
        .fillna("Non renseigné")
        .astype(str)
        .str.strip()
        .replace({"": "Non renseigné"})
    )

    count_columns = [col for col in STATUS_COUNT_COLUMNS if col in work.columns]
    snapshot_columns = [group_col] + count_columns
    if not count_columns:
        fallback_columns = [c for c in ["Vigilance", "Risque"] if c in work.columns]
        snapshot_columns += fallback_columns

    client_level = build_unique_client_snapshot(work, snapshot_columns)
    if client_level.empty:
        return pd.DataFrame(columns=output_columns)

    grouped = client_level.groupby(group_col, dropna=False).agg(**{"Nb clients": ("cm_client_key", "nunique")}).reset_index()
    total_clients = int(client_level["cm_client_key"].nunique())

    for status_label, column_name in CONCENTRATION_VIGILANCE_PERCENT_COLUMNS:
        source_col = f"Nb {status_label}"
        if source_col in client_level.columns:
            grouped[column_name] = (
                client_level.groupby(group_col, dropna=False)[source_col]
                .sum()
                .reindex(grouped[group_col], fill_value=0)
                .to_numpy()
            )
        else:
            grouped[column_name] = (
                client_level.groupby(group_col, dropna=False)["Vigilance"]
                .apply(lambda s, target=status_label: s.astype("string").eq(target).sum(), target=status_label)
                .reindex(grouped[group_col], fill_value=0)
                .to_numpy()
                if "Vigilance" in client_level.columns
                else 0
            )

    for status_label, column_name in CONCENTRATION_RISK_PERCENT_COLUMNS:
        source_col = f"Nb {status_label}"
        if source_col in client_level.columns:
            grouped[column_name] = (
                client_level.groupby(group_col, dropna=False)[source_col]
                .sum()
                .reindex(grouped[group_col], fill_value=0)
                .to_numpy()
            )
        else:
            grouped[column_name] = (
                client_level.groupby(group_col, dropna=False)["Risque"]
                .apply(lambda s, target=status_label: s.astype("string").eq(target).sum(), target=status_label)
                .reindex(grouped[group_col], fill_value=0)
                .to_numpy()
                if "Risque" in client_level.columns
                else 0
            )

    grouped["% clients"] = grouped["Nb clients"].div(total_clients if total_clients else np.nan).fillna(0.0)

    for status_label, column_name in CONCENTRATION_VIGILANCE_PERCENT_COLUMNS:
        source_col = f"Nb {status_label}"
        if source_col in client_level.columns:
            denominator = int(pd.to_numeric(client_level[source_col], errors="coerce").fillna(0).sum())
        else:
            denominator = int(client_level["Vigilance"].astype("string").eq(status_label).sum()) if "Vigilance" in client_level.columns else 0
        grouped[column_name] = pd.to_numeric(grouped[column_name], errors="coerce").fillna(0).div(denominator if denominator else np.nan).fillna(0.0)

    for status_label, column_name in CONCENTRATION_RISK_PERCENT_COLUMNS:
        source_col = f"Nb {status_label}"
        if source_col in client_level.columns:
            denominator = int(pd.to_numeric(client_level[source_col], errors="coerce").fillna(0).sum())
        else:
            denominator = int(client_level["Risque"].astype("string").eq(status_label).sum()) if "Risque" in client_level.columns else 0
        grouped[column_name] = pd.to_numeric(grouped[column_name], errors="coerce").fillna(0).div(denominator if denominator else np.nan).fillna(0.0)

    grouped = grouped.rename(columns={group_col: group_label})
    grouped = sort_concentration_top_table(grouped, group_label, sort_mode)
    return grouped[output_columns].head(top_n).reset_index(drop=True)


def strip_leading_status_prefix(value: object, prefix: str) -> object:
    if value is None or (isinstance(value, float) and np.isnan(value)) or pd.isna(value):
        return value
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return value
    cleaned = re.sub(rf"^{re.escape(prefix)}\s+", "", text, flags=re.IGNORECASE).strip()
    if cleaned != text and cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned or text


def build_priority_table(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    priority = df.copy()
    if priority.empty:
        return build_portfolio_underlying_table(
            priority,
            include_hidden_societe=True,
            display_columns_only=True,
            product_label="Produits",
        )

    priority = priority.sort_values(["Score priorité", SOC_COL, "SIREN"], ascending=[False, True, False], kind="stable")
    priority = build_unique_client_snapshot(priority)
    priority = priority.drop(columns=["cm_client_key"], errors="ignore").head(top_n).copy()
    return build_portfolio_underlying_table(
        priority,
        include_hidden_societe=True,
        display_columns_only=True,
        product_label="Produits",
    )


def build_portfolio_underlying_table(
    df: pd.DataFrame,
    *,
    include_hidden_societe: bool = True,
    strip_status_prefixes: bool = True,
    display_columns_only: bool = False,
    product_label: str = "Produit",
) -> pd.DataFrame:
    table = df.copy()
    if table is None or table.empty:
        return table

    if strip_status_prefixes:
        if "Vigilance" in table.columns:
            table["Vigilance"] = table["Vigilance"].apply(lambda value: strip_leading_status_prefix(value, "Vigilance"))
        if "Risque" in table.columns:
            table["Risque"] = table["Risque"].apply(lambda value: strip_leading_status_prefix(value, "Risque"))

    if include_hidden_societe and SOC_COL in table.columns:
        table["__societe_id"] = table[SOC_COL]

    base_columns = [
        "SIREN",
        "Dénomination",
        "Vigilance",
        "Risque",
        "Segment",
        "Pays de résidence",
        "Produit(service) principal",
        "Canal d’opérations principal 12 mois",
    ]
    preferred = list(base_columns)
    if not display_columns_only:
        preferred.extend([*VIGILANCE_COUNT_COLUMNS, *RISK_COUNT_COLUMNS])
    technical = ["__societe_id"] if "__societe_id" in table.columns else []
    excluded = {SOC_COL, *technical}
    remaining = [] if display_columns_only else [c for c in table.columns if c not in preferred and c not in excluded]
    columns = [c for c in preferred if c in table.columns] + remaining + technical

    return table[columns].rename(
        columns={
            "Pays de résidence": "Pays",
            "Produit(service) principal": product_label,
            "Canal d’opérations principal 12 mois": "Canaux",
        }
    )


def infer_portfolio_shared_column_widths(columns: list[str]) -> dict[str, str | None]:
    widths: dict[str, str | None] = {}
    for col in columns:
        if str(col).startswith("__"):
            continue
        if col == "SIREN":
            widths[col] = "small"
        elif col in {"Dénomination", "Client", "Produit", "Produits", "Canaux"}:
            widths[col] = "large"
        elif col in {"Vigilance", "Risque", "Statut", SOC_COL, "Société", "Segment", "Pays"}:
            widths[col] = "medium"
        elif col in {"Nb", "%", "#", "Rang", "Score", "Score priorité"}:
            widths[col] = "small"
        else:
            widths[col] = "medium"
    return widths


def format_percent_column(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    if "%" in output.columns:
        output["%"] = output["%"].map(lambda x: f"{x:.1%}")
    return output


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    export = df.copy()
    for col in export.columns:
        if pd.api.types.is_datetime64_any_dtype(export[col]):
            export[col] = export[col].dt.strftime("%Y-%m-%d")
    return export.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")


def dataframe_to_export_copy(df: pd.DataFrame) -> pd.DataFrame:
    export = df.copy()
    for col in export.columns:
        if pd.api.types.is_datetime64_any_dtype(export[col]):
            export[col] = export[col].dt.strftime("%Y-%m-%d")
    return export


def _safe_excel_sheet_name(name: str, fallback: str = "Feuille") -> str:
    safe = re.sub(r"[\/*?:\[\]]", " ", str(name or fallback)).strip()
    safe = safe or fallback
    return safe[:31]


def dataframes_to_excel_bytes(sheets: list[tuple[str, pd.DataFrame]]) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        workbook = writer.book
        header_format = workbook.add_format({
            "bold": True,
            "font_color": "#FFFFFF",
            "bg_color": "#1F5B94",
            "border": 0,
            "valign": "top",
            "text_wrap": True,
        })
        percent_format = workbook.add_format({"num_format": "0.0%"})
        integer_format = workbook.add_format({"num_format": "0"})
        date_format = workbook.add_format({"num_format": "dd/mm/yyyy"})

        used_sheet_names: set[str] = set()
        for index, (sheet_name, df) in enumerate(sheets, start=1):
            base_name = _safe_excel_sheet_name(sheet_name, fallback=f"Feuille {index}")
            safe_name = base_name
            suffix = 2
            while safe_name in used_sheet_names:
                suffix_label = f" ({suffix})"
                safe_name = f"{base_name[: max(1, 31 - len(suffix_label))]}{suffix_label}"
                suffix += 1
            used_sheet_names.add(safe_name)

            export_df = dataframe_to_export_copy(df)
            export_df.to_excel(writer, sheet_name=safe_name, index=False)
            worksheet = writer.sheets[safe_name]
            worksheet.hide_gridlines(2)

            num_rows, num_cols = export_df.shape
            if num_cols > 0:
                worksheet.freeze_panes(1, 0)
                worksheet.autofilter(0, 0, max(num_rows, 1), num_cols - 1)
                worksheet.set_row(0, 26, header_format)

            percent_columns = {
                col_idx
                for col_idx, column_name in enumerate(export_df.columns)
                if str(column_name).strip().startswith("%")
                or "% " in str(column_name)
            }

            for col_idx, column_name in enumerate(export_df.columns):
                worksheet.write(0, col_idx, column_name, header_format)
                values = [str(column_name)]
                values.extend(
                    "" if value is None or (isinstance(value, float) and pd.isna(value)) else str(value)
                    for value in export_df.iloc[:, col_idx].tolist()
                )
                max_length = max((len(value) for value in values), default=0)
                width = min(max(max_length + 2, 10), 42)

                column_series = export_df.iloc[:, col_idx] if num_cols > 0 else pd.Series(dtype="object")
                if col_idx in percent_columns:
                    worksheet.set_column(col_idx, col_idx, width, percent_format)
                    if num_rows > 0:
                        worksheet.conditional_format(1, col_idx, num_rows, col_idx, {
                            "type": "3_color_scale",
                            "min_color": "#FDECEC",
                            "mid_color": "#FFF2CC",
                            "max_color": "#D9EAD3",
                        })
                elif pd.api.types.is_datetime64_any_dtype(column_series):
                    worksheet.set_column(col_idx, col_idx, width, date_format)
                elif pd.api.types.is_integer_dtype(column_series) or pd.api.types.is_bool_dtype(column_series):
                    worksheet.set_column(col_idx, col_idx, width, integer_format)
                else:
                    worksheet.set_column(col_idx, col_idx, width)

    buffer.seek(0)
    return buffer.getvalue()



def committee_pack_download_name(selected_societies: list[str]) -> str:
    cleaned = [committee_report_slug(item)[:18] for item in selected_societies if str(item or "").strip()]
    if len(cleaned) > 2:
        scope_key = "_".join(cleaned[:2]) + f"_plus_{len(cleaned) - 2}"
    else:
        scope_key = "_".join(cleaned) or "portefeuille"
    return f"pack_comite_risques_{scope_key}_{datetime.now().strftime('%Y%m%d')}.xlsx"



def build_committee_pack_excel_bytes(
    *,
    selected_societies: list[str],
    filters: dict[str, object],
    sheets: list[tuple[str, pd.DataFrame]],
) -> bytes:
    summary_rows = [
        ("Périmètre", committee_report_scope_label(selected_societies)),
        ("Généré le", datetime.now().strftime('%d/%m/%Y %H:%M')),
        ("Filtres actifs", committee_report_filters_label(filters)),
        ("Onglets inclus", ", ".join(sheet_name for sheet_name, _ in sheets)),
    ]
    pack_sheets = [("Synthèse", pd.DataFrame(summary_rows, columns=["Rubrique", "Valeur"]))]
    pack_sheets.extend(sheets)
    return dataframes_to_excel_bytes(pack_sheets)



def analysis_committee_pack_download_name(selected_societies: list[str]) -> str:
    cleaned = [committee_report_slug(item)[:18] for item in selected_societies if str(item or "").strip()]
    if len(cleaned) > 2:
        scope_key = "_".join(cleaned[:2]) + f"_plus_{len(cleaned) - 2}"
    else:
        scope_key = "_".join(cleaned) or "analyse"
    return f"pack_comite_risques_analyse_{scope_key}_{datetime.now().strftime('%Y%m%d')}.xlsx"


def analysis_committee_report_download_name(selected_societies: list[str]) -> str:
    cleaned = [committee_report_slug(item)[:18] for item in selected_societies if str(item or "").strip()]
    if len(cleaned) > 2:
        scope_key = "_".join(cleaned[:2]) + f"_plus_{len(cleaned) - 2}"
    else:
        scope_key = "_".join(cleaned) or "analyse"
    return f"rapport_comite_risques_analyse_{scope_key}_{datetime.now().strftime('%Y%m%d')}.pdf"


@st.cache_data(show_spinner=False)
def build_analysis_committee_pack_excel_bytes(
    *,
    selected_societies: list[str],
    portfolio_filters: dict[str, object],
    indicator_filters: dict[str, object],
    sort_mode: str,
    filtered_portfolio: pd.DataFrame,
    filtered_indicators: pd.DataFrame,
    analysis_client_scope: pd.DataFrame,
    status_distribution: pd.DataFrame,
    family_distribution: pd.DataFrame,
    freshness_distribution: pd.DataFrame,
    top_segment_df: pd.DataFrame,
    top_pays_df: pd.DataFrame,
    top_produits_df: pd.DataFrame,
    top_canaux_df: pd.DataFrame,
    indicator_table: pd.DataFrame,
    analysis_table: pd.DataFrame,
) -> bytes:
    portfolio_active_filters = committee_report_filters_label(portfolio_filters)
    indicator_active_filters = committee_report_filters_label(indicator_filters)
    total_clients_portfolio = int(build_unique_client_snapshot(filtered_portfolio, [SOC_COL, "SIREN"]).shape[0])
    total_clients_scope = int(build_unique_client_snapshot(analysis_client_scope, [SOC_COL, "SIREN"]).shape[0])
    total_cases = int(len(filtered_indicators)) if filtered_indicators is not None else 0
    total_indicators = int(filtered_indicators.get("Indicateur", pd.Series(dtype="object")).astype(str).replace({"": pd.NA}).dropna().nunique()) if filtered_indicators is not None else 0
    last_update = pd.to_datetime(filtered_indicators.get("Date de mise à jour"), errors="coerce").max() if filtered_indicators is not None and "Date de mise à jour" in filtered_indicators.columns else pd.NaT
    last_update_label = pd.Timestamp(last_update).strftime('%d/%m/%Y') if pd.notna(last_update) else "Non disponible"

    summary_rows = [
        ("Écran source", "Analyse des indicateurs d’alerte"),
        ("Périmètre", committee_report_scope_label(selected_societies)),
        ("Généré le", datetime.now().strftime('%d/%m/%Y %H:%M')),
        ("Filtres portefeuille", portfolio_active_filters),
        ("Filtres indicateurs", indicator_active_filters),
        ("Tri des tops", sort_mode or "Nb"),
        ("Clients portefeuille filtré", total_clients_portfolio),
        ("Clients avec indicateurs", total_clients_scope),
        ("Cas indicateurs", total_cases),
        ("Indicateurs distincts", total_indicators),
        ("Dernière mise à jour visible", last_update_label),
        (
            "Onglets inclus",
            "Répartitions, tops par famille, indicateurs contributifs, tableau d’analyse, clients scope et cas indicateurs",
        ),
    ]

    client_columns = [
        SOC_COL,
        "SIREN",
        "Dénomination",
        "Vigilance",
        "Risque",
        "Segment",
        "Pays de résidence",
        "Produit(service) principal",
        "Canal d’opérations principal 12 mois",
        "Statut EDD",
        "Analyste",
        "Valideur",
        "Date dernière revue",
        "Date prochaine revue",
        "Vigilance Date de mise à jour",
    ]
    analysis_clients_export = build_unique_client_snapshot(analysis_client_scope, client_columns).drop(columns=["cm_client_key"], errors="ignore")

    indicator_case_columns = [
        SOC_COL,
        "SIREN",
        "Dénomination",
        "Indicateur",
        "Famille indicateur",
        "Statut",
        "Valeur",
        "Date de mise à jour",
        "Fraîcheur indicateur",
        "Commentaire",
        "Segment",
        "Pays de résidence",
        "Produit(service) principal",
        "Canal d’opérations principal 12 mois",
        "Analyste",
        "Valideur",
    ]
    indicator_cases_export = filtered_indicators[[col for col in indicator_case_columns if col in filtered_indicators.columns]].copy() if filtered_indicators is not None else pd.DataFrame(columns=indicator_case_columns)

    sheets = [
        ("Synthèse", pd.DataFrame(summary_rows, columns=["Rubrique", "Valeur"])),
        ("Répartition statuts", status_distribution.copy()),
        ("Répartition familles", family_distribution.copy()),
        ("Répartition fraîcheur", freshness_distribution.copy()),
        ("Top segment client", top_segment_df.copy()),
        ("Top pays", top_pays_df.copy()),
        ("Top produits", top_produits_df.copy()),
        ("Top canaux", top_canaux_df.copy()),
        ("Indicateurs contributifs", indicator_table.copy()),
        ("Tableau analyse", analysis_table.copy()),
        ("Clients scope", analysis_clients_export),
        ("Cas indicateurs", indicator_cases_export),
    ]
    return dataframes_to_excel_bytes(sheets)



def analysis_committee_report_prepare_top_table(df: pd.DataFrame, *, max_rows: int = 8) -> pd.DataFrame:
    columns = [
        "Indicateurs",
        "Nb",
        "%",
        "Nb avéré",
        "% avéré",
        "Nb potentiel",
        "% potentiel",
        "Nb NC",
        "% NC",
        "Nb sans risque",
        "% sans risque",
    ]
    if df is None or df.empty:
        return pd.DataFrame(columns=columns)
    available = [col for col in columns if col in df.columns]
    export = df[available].copy().head(max_rows)
    return export.reset_index(drop=True)



def analysis_committee_report_prepare_indicator_table(indicator_table: pd.DataFrame, *, max_rows: int = 10) -> pd.DataFrame:
    columns = ["Indicateur"] + ANALYSIS_STATUS_ORDER + ["Total cas"]
    if indicator_table is None or indicator_table.empty:
        return pd.DataFrame(columns=["Indicateur"] + [analysis_status_ui_label(status) for status in ANALYSIS_STATUS_ORDER] + ["Total cas"])
    export = indicator_table[[col for col in columns if col in indicator_table.columns]].copy().head(max_rows)
    export = export.rename(columns={status: analysis_status_ui_label(status) for status in ANALYSIS_STATUS_ORDER})
    return export.reset_index(drop=True)



def analysis_committee_report_prepare_clients_table(indicator_df: pd.DataFrame, *, max_rows: int = 12) -> pd.DataFrame:
    columns = ["SIREN", "Dénomination", "Cas", "Indicateurs distincts", "Statut dominant", "Famille dominante", "Indicateurs clés"]
    if indicator_df is None or indicator_df.empty:
        return pd.DataFrame(columns=columns)

    group_cols = [col for col in [SOC_COL, "SIREN", "Dénomination"] if col in indicator_df.columns]
    if not group_cols:
        return pd.DataFrame(columns=columns)

    rows: list[dict[str, object]] = []
    for keys, group in indicator_df.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        mapping = dict(zip(group_cols, keys))
        status_counts = group.get("Statut", pd.Series(dtype="object")).astype(str).value_counts()
        dominant_status = ""
        if not status_counts.empty:
            ordered_statuses = sorted(
                status_counts.items(),
                key=lambda item: (-int(item[1]), ANALYSIS_STATUS_ORDER.index(item[0]) if item[0] in ANALYSIS_STATUS_ORDER else 999, str(item[0])),
            )
            dominant_status = analysis_status_ui_label(ordered_statuses[0][0])

        family_counts = group.get("Famille indicateur", pd.Series(dtype="object")).astype(str).value_counts()
        dominant_family = str(family_counts.index[0]) if not family_counts.empty else ""
        indicator_names = [str(name).strip() for name in group.get("Indicateur", pd.Series(dtype="object")).astype(str).value_counts().head(3).index if str(name).strip()]
        rows.append({
            "SIREN": mapping.get("SIREN", ""),
            "Dénomination": mapping.get("Dénomination", ""),
            "Cas": int(len(group)),
            "Indicateurs distincts": int(group.get("Indicateur", pd.Series(dtype="object")).astype(str).replace({"": pd.NA}).dropna().nunique()),
            "Statut dominant": dominant_status,
            "Famille dominante": dominant_family,
            "Indicateurs clés": ", ".join(indicator_names),
        })

    export = pd.DataFrame(rows)
    if export.empty:
        return pd.DataFrame(columns=columns)
    export = export.sort_values(["Cas", "Indicateurs distincts", "Dénomination"], ascending=[False, False, True], kind="stable")
    return export[columns].head(max_rows).reset_index(drop=True)



def analysis_committee_report_top_commentary(title: str, df: pd.DataFrame, sort_mode: str) -> str:
    if df is None or df.empty:
        return f"Aucun indicateur exploitable n’est disponible sur {title.lower()}."
    first_row = df.iloc[0]
    indicator_name = committee_report_format_scalar(first_row.get("Indicateurs"), "Indicateurs")
    metric_column = sort_mode if sort_mode in df.columns else "Nb"
    metric_value = committee_report_format_scalar(first_row.get(metric_column), metric_column)
    extra_parts: list[str] = []
    for column_name in ["% avéré", "% potentiel", "% NC", "% sans risque"]:
        if column_name in df.columns:
            current_value = committee_report_numeric(first_row.get(column_name))
            if current_value > 0:
                extra_parts.append(f"{committee_report_format_scalar(current_value, column_name)} en {column_name.replace('% ', '').lower()}")
    extra_label = " ; ".join(extra_parts[:2]) if extra_parts else ""
    sentence = f"Sur {title.lower()}, l’indicateur {indicator_name} arrive en tête selon le tri {metric_column.lower()} avec {metric_value}."
    if extra_label:
        sentence += f" Lecture complémentaire : {extra_label}."
    return sentence



def analysis_committee_report_find_primary_signal(top_sections: list[tuple[str, pd.DataFrame]], sort_mode: str) -> str:
    best_message = "Aucune poche d’alerte significative n’a pu être mise en évidence sur le périmètre filtré."
    best_value = -1.0
    for title, df in top_sections:
        if df is None or df.empty:
            continue
        metric_column = sort_mode if sort_mode in df.columns else "Nb"
        row = df.iloc[0]
        current_value = committee_report_numeric(row.get(metric_column))
        if current_value > best_value:
            best_value = current_value
            best_message = analysis_committee_report_top_commentary(title, df, sort_mode)
    return best_message



def analysis_committee_report_key_messages(
    metrics: dict[str, object],
    top_sections: list[tuple[str, pd.DataFrame]],
    indicator_table: pd.DataFrame,
    sort_mode: str,
) -> list[str]:
    concerned_clients = int(metrics.get("concerned_clients", 0) or 0)
    total_clients_filtered = int(metrics.get("total_clients_filtered", 0) or 0)
    total_cases = int(metrics.get("total_cases", 0) or 0)
    distinct_indicators = int(metrics.get("distinct_indicators", 0) or 0)
    avers = int(metrics.get("risk_avere", 0) or 0)
    potentials = int(metrics.get("risk_potentiel", 0) or 0)
    non_calculable = int(metrics.get("risk_nc", 0) or 0)
    sans_risque = int(metrics.get("risk_sans", 0) or 0)
    stale_cases = int(metrics.get("stale_cases", 0) or 0)
    no_date_cases = int(metrics.get("no_date_cases", 0) or 0)

    messages: list[str] = []
    if total_clients_filtered:
        share_clients = concerned_clients / total_clients_filtered if total_clients_filtered else 0.0
        messages.append(
            f"Le périmètre analysé couvre {concerned_clients} clients concernés sur {total_clients_filtered} clients du portefeuille filtré ({committee_report_format_scalar(share_clients, '%')})."
        )
    if total_cases or distinct_indicators:
        messages.append(
            f"{total_cases} cas indicateurs sont visibles, portés par {distinct_indicators} indicateurs distincts ; c’est la base de lecture du présent rapport."
        )
    sensitive_cases = avers + potentials + non_calculable
    if total_cases:
        sensitive_share = sensitive_cases / total_cases if total_cases else 0.0
        messages.append(
            f"Les statuts sensibles (avéré, potentiel, non calculable) représentent {sensitive_cases} cas, soit {committee_report_format_scalar(sensitive_share, '%')} des alertes visibles."
        )
    if sans_risque > 0:
        safe_share = sans_risque / total_cases if total_cases else 0.0
        messages.append(
            f"{sans_risque} cas relèvent d’un statut sans risque, soit {committee_report_format_scalar(safe_share, '%')} du périmètre indicateurs ; ce volume doit être lu en miroir des poches sensibles."
        )
    if stale_cases > 0 or no_date_cases > 0:
        fragments = []
        if stale_cases > 0:
            fragments.append(f"{stale_cases} cas anciens (> 90 jours)")
        if no_date_cases > 0:
            fragments.append(f"{no_date_cases} cas sans date de mise à jour")
        messages.append("La fraîcheur des alertes appelle une vigilance particulière : " + " et ".join(fragments) + ".")

    messages.append(analysis_committee_report_find_primary_signal(top_sections, sort_mode))

    if indicator_table is not None and not indicator_table.empty and "Indicateur" in indicator_table.columns:
        head_names = [str(name).strip() for name in indicator_table["Indicateur"].head(3).tolist() if str(name or "").strip()]
        if head_names:
            if len(head_names) == 1:
                names_text = head_names[0]
            elif len(head_names) == 2:
                names_text = f"{head_names[0]} et {head_names[1]}"
            else:
                names_text = ", ".join(head_names[:-1]) + f" et {head_names[-1]}"
            messages.append(f"Les indicateurs les plus contributifs du périmètre sont : {names_text}.")

    return messages[:5]



def analysis_committee_report_decision_points(
    metrics: dict[str, object],
    top_sections: list[tuple[str, pd.DataFrame]],
    indicator_table: pd.DataFrame,
    sort_mode: str,
) -> list[str]:
    decisions: list[str] = []
    if int(metrics.get("risk_avere", 0) or 0) > 0:
        decisions.append("Arbitrer les actions à conduire sur les cas en risque avéré et confirmer les priorités de remédiation les plus immédiates.")
    if int(metrics.get("risk_potentiel", 0) or 0) > 0:
        decisions.append("Hiérarchiser les cas en risque potentiel afin de cibler les revues ou approfondissements à lancer à court terme.")
    if int(metrics.get("risk_nc", 0) or 0) > 0:
        decisions.append("Fiabiliser les cas non calculables pour réduire les angles morts de lecture avant le prochain comité.")
    if int(metrics.get("stale_cases", 0) or 0) > 0 or int(metrics.get("no_date_cases", 0) or 0) > 0:
        decisions.append("Mettre sous pilotage la fraîcheur des alertes afin d’éviter qu’une part du périmètre repose sur des signaux anciens ou non datés.")
    primary_signal = analysis_committee_report_find_primary_signal(top_sections, sort_mode)
    if primary_signal:
        decisions.append("Suivre au prochain comité la famille d’indicateurs la plus contributive et les poches de concentration qui lui sont liées.")
    if indicator_table is not None and not indicator_table.empty:
        decisions.append("Documenter, pour les indicateurs les plus contributifs, les mesures déjà prises et les actions complémentaires à décider en séance.")

    default_items = [
        "Conserver le pack Excel en annexe de travail pour l’analyse détaillée et la traçabilité post-séance.",
        "Formaliser les propriétaires d’action pour chaque poche d’alerte retenue en séance.",
    ]
    for item in default_items:
        if len(decisions) >= 5:
            break
        decisions.append(item)
    return decisions[:5]



def build_analysis_committee_report_pdf_bytes(
    *,
    selected_societies: list[str],
    portfolio_filters: dict[str, object],
    indicator_filters: dict[str, object],
    sort_mode: str,
    filtered_portfolio: pd.DataFrame,
    filtered_indicators: pd.DataFrame,
    analysis_client_scope: pd.DataFrame,
    status_distribution: pd.DataFrame,
    family_distribution: pd.DataFrame,
    freshness_distribution: pd.DataFrame,
    top_segment_df: pd.DataFrame,
    top_pays_df: pd.DataFrame,
    top_produits_df: pd.DataFrame,
    top_canaux_df: pd.DataFrame,
    indicator_table: pd.DataFrame,
    analysis_table: pd.DataFrame,
) -> bytes:
    if not REPORTLAB_AVAILABLE or SimpleDocTemplate is None or colors is None or mm is None or PageBreak is None:
        raise ModuleNotFoundError(PDF_DEPENDENCY_ERROR_MESSAGE)

    styles = committee_report_pdf_styles()
    generated_at = datetime.now()

    concerned_clients = int(build_unique_client_snapshot(analysis_client_scope).shape[0]) if isinstance(analysis_client_scope, pd.DataFrame) else 0
    total_clients_filtered = int(build_unique_client_snapshot(filtered_portfolio).shape[0]) if isinstance(filtered_portfolio, pd.DataFrame) else 0
    total_cases = int(len(filtered_indicators)) if isinstance(filtered_indicators, pd.DataFrame) else 0
    distinct_indicators = int(filtered_indicators.get("Indicateur", pd.Series(dtype="object")).astype(str).replace({"": pd.NA}).dropna().nunique()) if isinstance(filtered_indicators, pd.DataFrame) else 0
    last_update = pd.to_datetime(filtered_indicators.get("Date de mise à jour"), errors="coerce").max() if isinstance(filtered_indicators, pd.DataFrame) and "Date de mise à jour" in filtered_indicators.columns else pd.NaT
    stale_cases = int(filtered_indicators.get("Fraîcheur indicateur", pd.Series(dtype="object")).astype(str).eq("> 90 jours").sum()) if isinstance(filtered_indicators, pd.DataFrame) else 0
    no_date_cases = int(filtered_indicators.get("Fraîcheur indicateur", pd.Series(dtype="object")).astype(str).eq("Sans date").sum()) if isinstance(filtered_indicators, pd.DataFrame) else 0
    status_series = filtered_indicators.get("Statut", pd.Series(dtype="object")) if isinstance(filtered_indicators, pd.DataFrame) else pd.Series(dtype="object")
    metrics = {
        "concerned_clients": concerned_clients,
        "total_clients_filtered": total_clients_filtered,
        "total_cases": total_cases,
        "distinct_indicators": distinct_indicators,
        "risk_avere": int(status_series.astype(str).eq("Risque avéré").sum()) if not status_series.empty else 0,
        "risk_potentiel": int(status_series.astype(str).eq("Risque potentiel").sum()) if not status_series.empty else 0,
        "risk_mitige": int(status_series.astype(str).eq("Risque mitigé").sum()) if not status_series.empty else 0,
        "risk_leve": int(status_series.astype(str).eq("Risque levé").sum()) if not status_series.empty else 0,
        "risk_nc": int(status_series.astype(str).eq("Non calculable").sum()) if not status_series.empty else 0,
        "risk_sans": int(status_series.astype(str).eq("Aucun risque détecté").sum()) if not status_series.empty else 0,
        "last_update": last_update,
        "stale_cases": stale_cases,
        "no_date_cases": no_date_cases,
    }

    scope_label = committee_report_scope_label(selected_societies)
    portfolio_filters_label = committee_report_filters_label(portfolio_filters)
    indicator_filters_label = committee_report_filters_label(indicator_filters)

    top_sections_raw = [
        ("Top segment / client", top_segment_df),
        ("Top pays", top_pays_df),
        ("Top produits", top_produits_df),
        ("Top canaux", top_canaux_df),
    ]
    top_sections = [(title, analysis_committee_report_prepare_top_table(df)) for title, df in top_sections_raw]
    key_messages = analysis_committee_report_key_messages(metrics, top_sections_raw, indicator_table, sort_mode)
    decision_points = analysis_committee_report_decision_points(metrics, top_sections_raw, indicator_table, sort_mode)
    indicator_pdf_df = analysis_committee_report_prepare_indicator_table(indicator_table)
    clients_pdf_df = analysis_committee_report_prepare_clients_table(filtered_indicators)
    analysis_excerpt_df = analysis_table.copy().head(12) if analysis_table is not None else pd.DataFrame()

    metric_cards = [
        ("Clients concernés", concerned_clients, "clients avec au moins 1 indicateur"),
        ("Cas indicateurs", total_cases, "occurrences visibles"),
        ("Indicateurs distincts", distinct_indicators, "indicateurs présents"),
        ("Risque avéré", metrics["risk_avere"], "cas classés avérés"),
        ("Risque potentiel", metrics["risk_potentiel"], "cas classés potentiels"),
        ("Non calculable", metrics["risk_nc"], "cas à fiabiliser"),
        ("Sans risque", metrics["risk_sans"], "cas sans risque détecté"),
    ]

    cover_metadata = {
        "Périmètre société": scope_label,
        "Filtres portefeuille": portfolio_filters_label,
        "Filtres indicateurs": indicator_filters_label,
        "Tri des tops": sort_mode or "Nb",
        "Date de génération": generated_at.strftime("%d/%m/%Y %H:%M"),
        "Clients concernés": concerned_clients,
        "Cas indicateurs": total_cases,
        "Dernière mise à jour visible": committee_report_format_scalar(last_update, "Date de mise à jour") if pd.notna(last_update) else "Non renseignée",
        "Version analyse": ANALYSIS_SCREEN_CACHE_VERSION,
    }

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=16 * mm,
        title=f"Rapport Comité des Risques - Analyse - {scope_label}",
        author=PAGE_TITLE,
        subject="Synthèse d’analyse des alertes pour comité des risques",
    )

    regular_font, _ = ensure_review_simulation_pdf_fonts()
    primary_color = colors.HexColor(PRIMARY_COLOR)
    muted_color = colors.HexColor("#5B6B7F")

    def _draw_page(canvas, doc_obj):
        canvas.saveState()
        canvas.setStrokeColor(primary_color)
        canvas.setLineWidth(0.9)
        canvas.line(doc_obj.leftMargin, A4[1] - 12 * mm, A4[0] - doc_obj.rightMargin, A4[1] - 12 * mm)
        canvas.setFont(regular_font, 8)
        canvas.setFillColor(muted_color)
        canvas.drawString(doc_obj.leftMargin, 10 * mm, f"{PAGE_TITLE} - Rapport Comité des Risques")
        canvas.drawRightString(A4[0] - doc_obj.rightMargin, 10 * mm, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()

    story: list[object] = [
        committee_report_paragraph("Document préparatoire", styles["cover_kicker"]),
        committee_report_paragraph("Rapport Comité des Risques", styles["cover_title"]),
        committee_report_paragraph(
            f"Analyse des alertes - {scope_label}\nGénéré le {generated_at.strftime('%d/%m/%Y à %H:%M')}",
            styles["cover_subtitle"],
        ),
        committee_report_message_box(
            "Finalité du document",
            [
                "Fournir une lecture exécutive des indicateurs d’alerte sur le périmètre filtré de l’écran Analyse.",
                "Mettre en évidence les statuts, familles d’indicateurs, concentrations et signaux les plus contributifs.",
                "Appuyer les arbitrages du Comité des Risques en complément du pack Excel détaillé généré depuis l’écran.",
            ],
            styles,
        ),
        Spacer(1, 7 * mm),
        committee_report_cover_table(cover_metadata, styles),
        PageBreak(),
        committee_report_paragraph("1. Synthèse exécutive", styles["section"]),
        committee_report_metric_grid(metric_cards, styles),
        Spacer(1, 6 * mm),
        committee_report_message_box("Messages clés", key_messages, styles),
        Spacer(1, 6 * mm),
        committee_report_message_box(
            "Lecture du rapport",
            [
                "Le document est calculé uniquement sur les filtres actifs de l’écran Analyse au moment de la génération.",
                "Les répartitions et tops présentés ici sont propres aux indicateurs d’alerte et n’impactent pas l’écran Portefeuille.",
            ],
            styles,
        ),
        PageBreak(),
        committee_report_paragraph("2. Panorama des alertes", styles["section"]),
        committee_report_paragraph("Répartition par statut", styles["subsection"]),
        committee_report_dataframe_table(status_distribution, styles, column_widths=[88 * mm, 34 * mm, 52 * mm]),
        Spacer(1, 4 * mm),
        committee_report_paragraph("Répartition par famille", styles["subsection"]),
        committee_report_dataframe_table(family_distribution, styles, column_widths=[78 * mm, 30 * mm, 30 * mm, 36 * mm]),
        Spacer(1, 4 * mm),
        committee_report_paragraph("Répartition par fraîcheur", styles["subsection"]),
        committee_report_dataframe_table(freshness_distribution, styles, column_widths=[88 * mm, 34 * mm, 52 * mm]),
        Spacer(1, 4 * mm),
        committee_report_message_box(
            "Lecture managériale",
            [
                f"Le périmètre d’analyse couvre {concerned_clients} clients concernés et {total_cases} cas indicateurs visibles.",
                f"La part des cas anciens ou non datés atteint {committee_report_format_scalar(((stale_cases + no_date_cases) / total_cases) if total_cases else 0.0, '%')} du périmètre indicateurs.",
                "Les sections suivantes détaillent les poches de concentration par famille d’indicateurs, puis les indicateurs et clients à suivre en priorité.",
            ],
            styles,
        ),
        PageBreak(),
        committee_report_paragraph("3. Concentrations des alertes", styles["section"]),
    ]

    for idx, (title, table_df) in enumerate(top_sections):
        if idx > 0:
            story.append(Spacer(1, 4 * mm))
        story.extend([
            committee_report_paragraph(title, styles["subsection"]),
            committee_report_dataframe_table(
                table_df,
                styles,
                column_widths=committee_report_auto_col_widths(table_df) if table_df is not None and not table_df.empty else None,
            ),
            Spacer(1, 2.5 * mm),
            committee_report_message_box("Lecture", [analysis_committee_report_top_commentary(title, top_sections_raw[idx][1], sort_mode)], styles),
        ])
        if idx in {1, 3} and idx < len(top_sections) - 1:
            story.append(PageBreak())

    story.extend([
        PageBreak(),
        committee_report_paragraph("4. Indicateurs les plus contributifs", styles["section"]),
        committee_report_message_box(
            "Principe de lecture",
            [
                "Le classement ci-dessous reprend les indicateurs qui contribuent le plus au volume de cas sur le périmètre filtré.",
                "La ventilation par statut permet d’identifier rapidement les indicateurs à dominante sensible, favorable ou non calculable.",
            ],
            styles,
        ),
        Spacer(1, 5 * mm),
        committee_report_dataframe_table(
            indicator_pdf_df,
            styles,
            column_widths=committee_report_auto_col_widths(indicator_pdf_df) if indicator_pdf_df is not None and not indicator_pdf_df.empty else None,
        ),
        Spacer(1, 5 * mm),
        committee_report_paragraph("5. Clients les plus exposés", styles["section"]),
        committee_report_dataframe_table(
            clients_pdf_df,
            styles,
            column_widths=[22 * mm, 52 * mm, 18 * mm, 28 * mm, 26 * mm, 30 * mm, 48 * mm],
        ),
        Spacer(1, 5 * mm),
        committee_report_paragraph("6. Décisions proposées au Comité", styles["section"]),
        committee_report_message_box("Décisions attendues", decision_points, styles),
        PageBreak(),
        committee_report_paragraph("Annexe - Extrait du tableau d’analyse", styles["section"]),
        committee_report_paragraph(
            "Cet extrait rappelle la lecture détaillée par dimensions. Le pack Excel généré depuis l’écran Analyse reste la référence détaillée pour l’exploitation opérationnelle.",
            styles["body_muted"],
        ),
        Spacer(1, 3 * mm),
        committee_report_dataframe_table(
            analysis_excerpt_df,
            styles,
            column_widths=committee_report_auto_col_widths(analysis_excerpt_df) if analysis_excerpt_df is not None and not analysis_excerpt_df.empty else None,
            max_rows=12,
        ),
    ])

    doc.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    pdf_value = buffer.getvalue()
    buffer.close()
    return pdf_value


def committee_report_slug(value: object) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^A-Za-z0-9]+", "_", normalized).strip("_").lower()
    return slug or "portefeuille"


def committee_report_download_name(selected_societies: list[str]) -> str:
    cleaned = [committee_report_slug(item)[:18] for item in selected_societies if str(item or "").strip()]
    if len(cleaned) > 2:
        scope_key = "_".join(cleaned[:2]) + f"_plus_{len(cleaned) - 2}"
    else:
        scope_key = "_".join(cleaned) or "portefeuille"
    return f"rapport_comite_risques_portefeuille_{scope_key}_{datetime.now().strftime('%Y%m%d')}.pdf"


def committee_report_scope_label(selected_societies: list[str]) -> str:
    cleaned = [str(item).strip() for item in selected_societies if str(item or "").strip()]
    if not cleaned:
        return "Périmètre non renseigné"
    if len(cleaned) <= 4:
        return ", ".join(cleaned)
    return ", ".join(cleaned[:4]) + f" (+{len(cleaned) - 4} autres)"


def committee_report_filters_label(filters: dict[str, object]) -> str:
    active = [f"{label} : {value}" for label, value in filters.items() if str(value) != "Tous"]
    return "Aucun filtre additionnel" if not active else " ; ".join(active)


def committee_report_format_scalar(value: object, column_name: object = "") -> str:
    try:
        if value is None or pd.isna(value):
            return "—"
    except Exception:
        pass

    if isinstance(value, (pd.Timestamp, datetime)):
        dt_value = pd.to_datetime(value, errors="coerce")
        if pd.isna(dt_value):
            return "—"
        return pd.Timestamp(dt_value).strftime("%d/%m/%Y")

    if isinstance(value, (np.integer, int)) and not isinstance(value, bool):
        return f"{int(value):,}".replace(",", " ")

    if isinstance(value, (np.floating, float)) and not isinstance(value, bool):
        number = float(value)
        column_text = str(column_name or "").strip()
        if column_text.startswith("%") and 0.0 <= number <= 1.0:
            return f"{number * 100:.1f} %".replace(".", ",")
        if abs(number - round(number)) < 1e-9:
            return f"{int(round(number)):,}".replace(",", " ")
        return f"{number:,.1f}".replace(",", " ").replace(".", ",")

    text_value = str(value).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text_value):
        dt_value = pd.to_datetime(text_value, errors="coerce")
        if not pd.isna(dt_value):
            return pd.Timestamp(dt_value).strftime("%d/%m/%Y")
    return text_value or "—"


def committee_report_numeric(value: object) -> float:
    try:
        if value is None or pd.isna(value):
            return 0.0
    except Exception:
        pass
    try:
        return float(value)
    except Exception:
        return 0.0


def committee_report_paragraph(text: object, style: ParagraphStyle) -> Paragraph:
    rendered = str(text or "").strip() or "—"
    return Paragraph(escape(rendered).replace("\n", "<br/>"), style)


def committee_report_pdf_styles() -> dict[str, ParagraphStyle]:
    if not REPORTLAB_AVAILABLE or colors is None or getSampleStyleSheet is None or ParagraphStyle is None:
        raise ModuleNotFoundError(PDF_DEPENDENCY_ERROR_MESSAGE)

    regular_font, bold_font = ensure_review_simulation_pdf_fonts()
    base_styles = getSampleStyleSheet()
    primary_color = colors.HexColor(PRIMARY_COLOR)
    secondary_color = colors.HexColor(SECONDARY_COLOR)
    muted_color = colors.HexColor("#5B6B7F")
    body_color = colors.HexColor("#12263A")

    return {
        "cover_kicker": ParagraphStyle(
            "CommitteeCoverKicker",
            parent=base_styles["BodyText"],
            fontName=bold_font,
            fontSize=10,
            leading=12,
            textColor=secondary_color,
            spaceAfter=6,
        ),
        "cover_title": ParagraphStyle(
            "CommitteeCoverTitle",
            parent=base_styles["Title"],
            fontName=bold_font,
            fontSize=23,
            leading=28,
            textColor=primary_color,
            spaceAfter=8,
        ),
        "cover_subtitle": ParagraphStyle(
            "CommitteeCoverSubtitle",
            parent=base_styles["BodyText"],
            fontName=regular_font,
            fontSize=10.5,
            leading=14,
            textColor=muted_color,
            spaceAfter=14,
        ),
        "section": ParagraphStyle(
            "CommitteeSection",
            parent=base_styles["Heading2"],
            fontName=bold_font,
            fontSize=13,
            leading=16,
            textColor=primary_color,
            spaceBefore=4,
            spaceAfter=7,
        ),
        "subsection": ParagraphStyle(
            "CommitteeSubsection",
            parent=base_styles["Heading3"],
            fontName=bold_font,
            fontSize=10.2,
            leading=12.5,
            textColor=primary_color,
            spaceBefore=2,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "CommitteeBody",
            parent=base_styles["BodyText"],
            fontName=regular_font,
            fontSize=9.2,
            leading=12.2,
            textColor=body_color,
        ),
        "body_muted": ParagraphStyle(
            "CommitteeBodyMuted",
            parent=base_styles["BodyText"],
            fontName=regular_font,
            fontSize=8.5,
            leading=11,
            textColor=muted_color,
        ),
        "table_header": ParagraphStyle(
            "CommitteeTableHeader",
            parent=base_styles["BodyText"],
            fontName=bold_font,
            fontSize=8.2,
            leading=10,
            textColor=colors.white,
        ),
        "table_cell": ParagraphStyle(
            "CommitteeTableCell",
            parent=base_styles["BodyText"],
            fontName=regular_font,
            fontSize=8.4,
            leading=10.4,
            textColor=body_color,
        ),
        "table_cell_small": ParagraphStyle(
            "CommitteeTableCellSmall",
            parent=base_styles["BodyText"],
            fontName=regular_font,
            fontSize=7.8,
            leading=9.6,
            textColor=body_color,
        ),
        "metric_card": ParagraphStyle(
            "CommitteeMetricCard",
            parent=base_styles["BodyText"],
            fontName=regular_font,
            fontSize=8.8,
            leading=11.2,
            textColor=body_color,
        ),
        "box_title": ParagraphStyle(
            "CommitteeBoxTitle",
            parent=base_styles["BodyText"],
            fontName=bold_font,
            fontSize=9.2,
            leading=11.8,
            textColor=primary_color,
        ),
    }


def committee_report_message_box(title: str, lines: list[str], styles: dict[str, ParagraphStyle], width: float = 174 * mm) -> Table:
    rows = [[committee_report_paragraph(title, styles["box_title"])]]
    for line in lines:
        rows.append([committee_report_paragraph(f"• {line}", styles["body"])])

    table = Table(rows, colWidths=[width], hAlign="LEFT", splitByRow=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4F8FD")),
        ("BOX", (0, 0), (-1, -1), 0.65, colors.HexColor("#C9D9EA")),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -2), 0.35, colors.HexColor("#D9E6F2")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def committee_report_metric_grid(metrics: list[tuple[str, object, str]], styles: dict[str, ParagraphStyle]) -> Table:
    cells: list[Paragraph] = []
    for label, value, note in metrics:
        value_text = committee_report_format_scalar(value, label)
        html = (
            f"<font color='{SECONDARY_COLOR}' size='8.2'><b>{escape(label)}</b></font><br/>"
            f"<font color='{PRIMARY_COLOR}' size='17'><b>{escape(value_text)}</b></font><br/>"
            f"<font color='#5B6B7F' size='7.6'>{escape(note)}</font>"
        )
        cells.append(Paragraph(html, styles["metric_card"]))

    rows: list[list[Paragraph]] = []
    for start in range(0, len(cells), 3):
        row = cells[start:start + 3]
        while len(row) < 3:
            row.append(Paragraph("", styles["metric_card"]))
        rows.append(row)

    table = Table(rows, colWidths=[58 * mm, 58 * mm, 58 * mm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFE")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D6E1EE")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D6E1EE")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def committee_report_auto_col_widths(df: pd.DataFrame, total_width: float = 174 * mm) -> list[float]:
    columns = [str(col) for col in df.columns]
    weights: list[float] = []
    for column_name in columns:
        if column_name in {"Dénomination", "Motifs", "Segment", "Pays", "Produit", "Canal", "Canaux", "Alerte"}:
            weights.append(2.8)
        elif column_name in {"Vigilance", "Risque", "Statut", "Indicateur", "Calcul / règle"}:
            weights.append(1.9)
        elif column_name.startswith("%") or column_name in {"Nb", "Nb clients", "Score priorité", "SIREN"}:
            weights.append(1.1)
        else:
            weights.append(1.5)
    total_weight = sum(weights) or 1.0
    return [total_width * weight / total_weight for weight in weights]


def committee_report_dataframe_table(
    df: pd.DataFrame,
    styles: dict[str, ParagraphStyle],
    *,
    column_widths: list[float] | None = None,
    max_rows: int | None = None,
) -> Table:
    if df is None or df.empty:
        return committee_report_message_box(
            "Aucune donnée disponible",
            ["Le périmètre filtré ne retourne aucune ligne exploitable pour cette section."],
            styles,
        )

    export = dataframe_to_export_copy(df.copy())
    export = export[[col for col in export.columns if not str(col).startswith("__")]]
    if max_rows is not None:
        export = export.head(max_rows)

    rows: list[list[Paragraph]] = [
        [committee_report_paragraph(column_name, styles["table_header"]) for column_name in export.columns]
    ]

    for _, record in export.iterrows():
        row_cells: list[Paragraph] = []
        for column_name in export.columns:
            rendered = committee_report_format_scalar(record[column_name], column_name)
            cell_style = styles["table_cell_small"] if column_name == "Motifs" or len(rendered) > 60 else styles["table_cell"]
            row_cells.append(committee_report_paragraph(rendered, cell_style))
        rows.append(row_cells)

    widths = column_widths or committee_report_auto_col_widths(export)
    table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT", splitByRow=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PRIMARY_COLOR)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFE")]),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D6E1EE")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def committee_report_trim_text(value: object, max_length: int = 120) -> str:
    rendered = str(value or "").strip()
    if len(rendered) <= max_length:
        return rendered or "—"
    shortened = rendered[: max_length - 1].rsplit(" ", 1)[0].strip()
    return (shortened or rendered[: max_length - 1].strip()) + "…"


def committee_report_prepare_priority_table(priority_df: pd.DataFrame) -> pd.DataFrame:
    if priority_df is None or priority_df.empty:
        return pd.DataFrame(columns=["SIREN", "Dénomination", "Vigilance", "Risque", "Score priorité", "Motifs"])
    wanted = [column for column in ["SIREN", "Dénomination", "Vigilance", "Risque", "Score priorité", "Motifs"] if column in priority_df.columns]
    output = priority_df[wanted].copy()
    if "Motifs" in output.columns:
        output["Motifs"] = output["Motifs"].apply(lambda value: committee_report_trim_text(value, max_length=120))
    return output


def committee_report_prepare_filtered_excerpt(filtered_export_df: pd.DataFrame) -> pd.DataFrame:
    if filtered_export_df is None or filtered_export_df.empty:
        return pd.DataFrame(columns=["SIREN", "Dénomination", "Vigilance", "Risque", "Segment", "Pays"])
    wanted = [column for column in ["SIREN", "Dénomination", "Vigilance", "Risque", "Segment", "Pays"] if column in filtered_export_df.columns]
    return filtered_export_df[wanted].head(12).copy()


def committee_report_prepare_concentration_table(df: pd.DataFrame, label_column: str) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=[label_column, "Nb clients", "% clients", "% Vig. crit.", "% Vig. élev.", "% Risq. av.", "% Risq. pot."])
    wanted = [
        column
        for column in [label_column, "Nb clients", "% clients", "% Vig. crit.", "% Vig. élev.", "% Risq. av.", "% Risq. pot."]
        if column in df.columns
    ]
    return df[wanted].head(5).copy()


def committee_report_concentration_status_label(column_name: str) -> str:
    return {
        "% Vig. crit.": "vigilance critique",
        "% Vig. élev.": "vigilance élevée",
        "% Risq. av.": "risque avéré",
        "% Risq. pot.": "risque potentiel",
        "% Risq. NC": "risque non calculable",
    }.get(column_name, str(column_name or "").replace("% ", "").lower())


def committee_report_find_primary_concentration(top_risks_export_sheets: list[tuple[str, pd.DataFrame]]) -> str:
    best_item: tuple[float, str] | None = None
    sensitive_columns = ["% Vig. crit.", "% Vig. élev.", "% Risq. av.", "% Risq. pot.", "% Risq. NC"]

    for title, df in top_risks_export_sheets:
        if df is None or df.empty:
            continue
        label_column = str(df.columns[0])
        for _, row in df.iterrows():
            base_weight = committee_report_numeric(row.get("% clients"))
            group_name = committee_report_format_scalar(row.get(label_column), label_column)
            for column_name in sensitive_columns:
                if column_name not in df.columns:
                    continue
                status_weight = committee_report_numeric(row.get(column_name))
                delta = status_weight - base_weight
                if delta <= 0:
                    continue
                message = (
                    f"La concentration la plus marquante concerne {title.lower()} « {group_name} » : "
                    f"{committee_report_format_scalar(base_weight, '% clients')} du portefeuille, mais "
                    f"{committee_report_format_scalar(status_weight, column_name)} du statut "
                    f"{committee_report_concentration_status_label(column_name)}."
                )
                if best_item is None or delta > best_item[0]:
                    best_item = (delta, message)

    if best_item is not None and best_item[0] > 0.04:
        return best_item[1]

    for title, df in top_risks_export_sheets:
        if df is None or df.empty:
            continue
        label_column = str(df.columns[0])
        first_row = df.iloc[0]
        group_name = committee_report_format_scalar(first_row.get(label_column), label_column)
        base_weight = committee_report_format_scalar(first_row.get("% clients"), "% clients")
        return f"La première poche de concentration se situe sur {title.lower()} « {group_name} », qui représente {base_weight} du portefeuille filtré."

    return "Aucune concentration particulière n’a pu être mise en évidence sur le périmètre filtré."


def committee_report_top_commentary(title: str, df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return f"Aucun signal exploitable n’est disponible sur {title.lower()}."
    label_column = str(df.columns[0])
    first_row = df.iloc[0]
    group_name = committee_report_format_scalar(first_row.get(label_column), label_column)
    base_weight = committee_report_numeric(first_row.get("% clients"))
    sensitive_columns = [column for column in ["% Vig. crit.", "% Vig. élev.", "% Risq. av.", "% Risq. pot."] if column in df.columns]
    best_column = None
    best_delta = 0.0
    best_value = 0.0
    for column_name in sensitive_columns:
        current_value = committee_report_numeric(first_row.get(column_name))
        current_delta = current_value - base_weight
        if current_delta > best_delta:
            best_delta = current_delta
            best_column = column_name
            best_value = current_value
    if best_column and best_delta > 0.04:
        return (
            f"{group_name} concentre {committee_report_format_scalar(base_weight, '% clients')} du portefeuille, "
            f"mais {committee_report_format_scalar(best_value, best_column)} du statut "
            f"{committee_report_concentration_status_label(best_column)}. Cette poche mérite une surveillance ciblée."
        )
    return (
        f"{group_name} constitue la première concentration sur {title.lower()} avec "
        f"{committee_report_format_scalar(base_weight, '% clients')} des clients visibles, sans surreprésentation sensible majeure."
    )


def committee_report_key_messages(
    metrics: dict[str, object],
    top_risks_export_sheets: list[tuple[str, pd.DataFrame]],
    priority_df: pd.DataFrame,
) -> list[str]:
    total = int(metrics.get("total_clients", 0) or 0)
    vigilance_renforcee = int(metrics.get("vigilance_renforcee", 0) or 0)
    risque_avere = int(metrics.get("risque_avere", 0) or 0)
    justificatifs = int(metrics.get("justificatifs_incomplets", 0) or 0)
    sans_revue = int(metrics.get("sans_prochaine_revue", 0) or 0)
    historique = int(metrics.get("historique_disponible", 0) or 0)

    messages: list[str] = []
    if total:
        part_vigilance = vigilance_renforcee / total
        tension_label = "forte" if part_vigilance >= 0.35 else "modérée" if part_vigilance >= 0.18 else "contenue"
        messages.append(
            f"Le portefeuille analysé couvre {total} clients uniques ; l’exposition en vigilance renforcée est {tension_label} "
            f"avec {vigilance_renforcee} clients concernés ({committee_report_format_scalar(part_vigilance, '%')})."
        )

    if risque_avere > 0:
        messages.append(
            f"{risque_avere} clients sont classés en risque avéré ; ces cas appellent un arbitrage explicite du comité sur la trajectoire de remédiation."
        )

    if justificatifs > 0 or sans_revue > 0:
        fragments: list[str] = []
        if justificatifs > 0:
            fragments.append(f"{justificatifs} justificatifs incomplets")
        if sans_revue > 0:
            fragments.append(f"{sans_revue} dossiers sans prochaine revue")
        messages.append(
            "La gouvernance portefeuille appelle une remise à niveau ciblée : " + " et ".join(fragments) + "."
        )

    if historique < total and total > 0:
        messages.append(
            f"L’historique disponible couvre {historique} clients ; la profondeur de traçabilité reste donc partielle sur une partie du portefeuille."
        )

    messages.append(committee_report_find_primary_concentration(top_risks_export_sheets))

    if priority_df is not None and not priority_df.empty and "Dénomination" in priority_df.columns:
        head_names = [str(name).strip() for name in priority_df["Dénomination"].head(3).tolist() if str(name or "").strip()]
        if head_names:
            if len(head_names) == 1:
                names_text = head_names[0]
            elif len(head_names) == 2:
                names_text = f"{head_names[0]} et {head_names[1]}"
            else:
                names_text = ", ".join(head_names[:-1]) + f" et {head_names[-1]}"
            messages.append(f"Les premiers dossiers à arbitrer en séance sont : {names_text}.")

    return messages[:5]


def committee_report_decision_points(
    metrics: dict[str, object],
    top_risks_export_sheets: list[tuple[str, pd.DataFrame]],
    priority_df: pd.DataFrame,
) -> list[str]:
    decisions: list[str] = []
    if priority_df is not None and not priority_df.empty:
        decisions.append("Valider l’ordre de traitement des dossiers prioritaires et confirmer les revues immédiates pour les cas les plus sensibles.")

    if int(metrics.get("justificatifs_incomplets", 0) or 0) > 0:
        decisions.append("Mandater un plan de complétude documentaire sur les dossiers renforcés présentant des justificatifs incomplets.")

    if int(metrics.get("sans_prochaine_revue", 0) or 0) > 0:
        decisions.append("Fiabiliser le calendrier des revues en imposant une date de prochaine revue sur chaque dossier non planifié.")

    concentration_message = committee_report_find_primary_concentration(top_risks_export_sheets)
    if concentration_message:
        decisions.append("Mettre sous surveillance renforcée la poche de concentration la plus exposée et suivre son évolution au prochain comité.")

    if int(metrics.get("risque_avere", 0) or 0) > 0:
        decisions.append("Arbitrer les mesures de remédiation ou de restriction sur les clients classés en risque avéré.")

    default_items = [
        "Conserver une lecture régulière de la répartition des vigilances et risques maximum sur le portefeuille filtré.",
        "S’appuyer sur les exports détaillés pour documenter le suivi opérationnel après séance.",
    ]
    for item in default_items:
        if len(decisions) >= 5:
            break
        decisions.append(item)
    return decisions[:5]


def committee_report_cover_table(metadata: dict[str, object], styles: dict[str, ParagraphStyle]) -> Table:
    rows = [
        [committee_report_paragraph("Repère", styles["table_header"]), committee_report_paragraph("Valeur", styles["table_header"])]
    ]
    for label, value in metadata.items():
        rows.append([
            committee_report_paragraph(label, styles["table_cell"]),
            committee_report_paragraph(committee_report_format_scalar(value, label), styles["table_cell"]),
        ])
    table = Table(rows, colWidths=[46 * mm, 128 * mm], repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PRIMARY_COLOR)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFE")]),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D6E1EE")),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def build_committee_risk_report_pdf_bytes(
    filtered: pd.DataFrame,
    selected_societies: list[str],
    filters: dict[str, object],
    vigilance_df: pd.DataFrame,
    risk_df: pd.DataFrame,
    alert_df: pd.DataFrame,
    top_risks_export_sheets: list[tuple[str, pd.DataFrame]],
    priority_df: pd.DataFrame,
    filtered_export_df: pd.DataFrame,
) -> bytes:
    if not REPORTLAB_AVAILABLE or SimpleDocTemplate is None or colors is None or mm is None or PageBreak is None:
        raise ModuleNotFoundError(PDF_DEPENDENCY_ERROR_MESSAGE)

    styles = committee_report_pdf_styles()
    generated_at = datetime.now()

    client_level = build_unique_client_snapshot(
        filtered,
        [
            "Vigilance",
            "Risque",
            "Alerte justificatif incomplet",
            "Alerte sans prochaine revue",
            "Nb historique",
            "Vigilance Date de mise à jour",
        ],
    )

    total_clients = len(client_level)
    vigilance_renforcee = int(client_level.get("Vigilance", pd.Series(dtype="object")).isin(CRITICAL_VIGILANCE).sum()) if total_clients else 0
    risque_avere = int(client_level.get("Risque", pd.Series(dtype="object")).eq("Risque avéré").sum()) if total_clients else 0
    justificatifs_incomplets = int(pd.to_numeric(client_level.get("Alerte justificatif incomplet", pd.Series(0, index=client_level.index)), errors="coerce").fillna(0).sum()) if total_clients else 0
    sans_prochaine_revue = int(pd.to_numeric(client_level.get("Alerte sans prochaine revue", pd.Series(0, index=client_level.index)), errors="coerce").fillna(0).sum()) if total_clients else 0
    historique_disponible = int(pd.to_numeric(client_level.get("Nb historique", pd.Series(0, index=client_level.index)), errors="coerce").fillna(0).gt(0).sum()) if total_clients else 0
    freshness_date = None
    if total_clients and "Vigilance Date de mise à jour" in client_level.columns:
        freshness_date = pd.to_datetime(client_level["Vigilance Date de mise à jour"], errors="coerce").max()

    metrics = {
        "total_clients": total_clients,
        "vigilance_renforcee": vigilance_renforcee,
        "risque_avere": risque_avere,
        "justificatifs_incomplets": justificatifs_incomplets,
        "sans_prochaine_revue": sans_prochaine_revue,
        "historique_disponible": historique_disponible,
        "fraicheur_visible": freshness_date,
    }

    scope_label = committee_report_scope_label(selected_societies)
    filters_label = committee_report_filters_label(filters)
    key_messages = committee_report_key_messages(metrics, top_risks_export_sheets, priority_df)
    decision_points = committee_report_decision_points(metrics, top_risks_export_sheets, priority_df)

    priority_pdf_df = committee_report_prepare_priority_table(priority_df)
    filtered_excerpt_df = committee_report_prepare_filtered_excerpt(filtered_export_df)

    top_sections = [
        (title, committee_report_prepare_concentration_table(df, str(df.columns[0]) if df is not None and not df.empty else title.replace("Top ", "")))
        for title, df in top_risks_export_sheets
    ]

    metric_cards = [
        ("Clients visibles", total_clients, "clients uniques du périmètre"),
        ("Vigilance renforcée", vigilance_renforcee, "vigilance élevée ou critique"),
        ("Risque avéré", risque_avere, "clients classés en risque avéré"),
        ("Justificatifs incomplets", justificatifs_incomplets, "alertes documentaires actives"),
        ("Sans prochaine revue", sans_prochaine_revue, "dossiers non planifiés"),
        ("Historique disponible", historique_disponible, "clients avec historique exploitable"),
    ]

    cover_metadata = {
        "Périmètre société": scope_label,
        "Filtres actifs": filters_label,
        "Date de génération": generated_at.strftime("%d/%m/%Y %H:%M"),
        "Clients visibles": total_clients,
        "Fraîcheur visible": committee_report_format_scalar(freshness_date, "Fraîcheur visible") if freshness_date is not None and not pd.isna(freshness_date) else "Non renseignée",
        "Version portefeuille": PORTFOLIO_PIPELINE_VERSION,
    }

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=16 * mm,
        title=f"Rapport Comité des Risques - {scope_label}",
        author=PAGE_TITLE,
        subject="Synthèse portefeuille pour comité des risques",
    )

    regular_font, _ = ensure_review_simulation_pdf_fonts()
    primary_color = colors.HexColor(PRIMARY_COLOR)
    muted_color = colors.HexColor("#5B6B7F")

    def _draw_page(canvas, doc_obj):
        canvas.saveState()
        canvas.setStrokeColor(primary_color)
        canvas.setLineWidth(0.9)
        canvas.line(doc_obj.leftMargin, A4[1] - 12 * mm, A4[0] - doc_obj.rightMargin, A4[1] - 12 * mm)
        canvas.setFont(regular_font, 8)
        canvas.setFillColor(muted_color)
        canvas.drawString(doc_obj.leftMargin, 10 * mm, f"{PAGE_TITLE} - Rapport Comité des Risques")
        canvas.drawRightString(A4[0] - doc_obj.rightMargin, 10 * mm, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()

    story: list[object] = [
        committee_report_paragraph("Document préparatoire", styles["cover_kicker"]),
        committee_report_paragraph("Rapport Comité des Risques", styles["cover_title"]),
        committee_report_paragraph(
            f"Portefeuille filtré - {scope_label}\nGénéré le {generated_at.strftime('%d/%m/%Y à %H:%M')}",
            styles["cover_subtitle"],
        ),
        committee_report_message_box(
            "Finalité du document",
            [
                "Fournir une lecture exécutive du portefeuille filtré à la date de génération.",
                "Mettre en évidence les expositions, concentrations, alertes de gouvernance et dossiers prioritaires.",
                "Appuyer les arbitrages du Comité des Risques sans se substituer aux exports détaillés disponibles dans l’écran.",
            ],
            styles,
        ),
        Spacer(1, 7 * mm),
        committee_report_cover_table(cover_metadata, styles),
        PageBreak(),
        committee_report_paragraph("1. Synthèse exécutive", styles["section"]),
        committee_report_metric_grid(metric_cards, styles),
        Spacer(1, 6 * mm),
        committee_report_message_box("Messages clés", key_messages, styles),
        Spacer(1, 6 * mm),
        committee_report_message_box(
            "Lecture du rapport",
            [
                "Le document est calculé uniquement sur le portefeuille filtré visible au moment de la génération.",
                "Les sections Répartition, Concentrations et Dossiers prioritaires reprennent les mêmes bases de calcul que les exports de l’écran.",
            ],
            styles,
        ),
        PageBreak(),
        committee_report_paragraph("2. Structure du portefeuille", styles["section"]),
        committee_report_paragraph("Répartition des vigilances", styles["subsection"]),
        committee_report_dataframe_table(vigilance_df, styles, column_widths=[90 * mm, 30 * mm, 34 * mm]),
        Spacer(1, 4 * mm),
        committee_report_paragraph("Répartition des risques maximum", styles["subsection"]),
        committee_report_dataframe_table(risk_df, styles, column_widths=[90 * mm, 30 * mm, 34 * mm]),
        Spacer(1, 4 * mm),
        committee_report_paragraph("Alertes de gouvernance", styles["subsection"]),
        committee_report_dataframe_table(alert_df, styles, column_widths=[120 * mm, 34 * mm]),
        Spacer(1, 4 * mm),
        committee_report_message_box(
            "Lecture managériale",
            [
                f"La vigilance renforcée concerne {vigilance_renforcee} clients sur {total_clients} ; elle matérialise le cœur de l’exposition portefeuille.",
                f"Les alertes de gouvernance restent concentrées sur {justificatifs_incomplets} justificatifs incomplets et {sans_prochaine_revue} dossiers sans prochaine revue.",
                "Les exports détaillés permettent ensuite de qualifier les écarts client par client si une action opérationnelle est décidée en séance.",
            ],
            styles,
        ),
        PageBreak(),
        committee_report_paragraph("3. Concentrations et poches de risque", styles["section"]),
    ]

    for idx, (title, table_df) in enumerate(top_sections):
        if idx > 0:
            story.append(Spacer(1, 4 * mm))
        story.extend([
            committee_report_paragraph(title, styles["subsection"]),
            committee_report_dataframe_table(
                table_df,
                styles,
                column_widths=committee_report_auto_col_widths(table_df) if not table_df.empty else None,
            ),
            Spacer(1, 2.5 * mm),
            committee_report_message_box("Lecture", [committee_report_top_commentary(title, table_df)], styles),
        ])

    story.extend([
        PageBreak(),
        committee_report_paragraph("4. Dossiers prioritaires", styles["section"]),
        committee_report_message_box(
            "Principe de lecture",
            [
                "Le classement ci-dessous reprend le top des dossiers priorisés sur le portefeuille filtré.",
                "Le score priorité agrège vigilance, risque et alertes actives afin d’ordonner les cas à traiter en premier.",
            ],
            styles,
        ),
        Spacer(1, 5 * mm),
        committee_report_dataframe_table(
            priority_pdf_df,
            styles,
            column_widths=[18 * mm, 48 * mm, 24 * mm, 26 * mm, 18 * mm, 40 * mm],
        ),
        Spacer(1, 5 * mm),
        committee_report_paragraph("5. Décisions proposées au Comité", styles["section"]),
        committee_report_message_box("Décisions attendues", decision_points, styles),
        PageBreak(),
        committee_report_paragraph("Annexe - Extrait de la vue filtrée", styles["section"]),
        committee_report_paragraph(
            "Cet extrait rappelle la physionomie du portefeuille filtré. Les exports CSV et Excel disponibles dans l’écran restent la référence détaillée pour l’analyse opérationnelle.",
            styles["body_muted"],
        ),
        Spacer(1, 3 * mm),
        committee_report_dataframe_table(
            filtered_excerpt_df,
            styles,
            column_widths=[18 * mm, 50 * mm, 24 * mm, 24 * mm, 28 * mm, 30 * mm],
        ),
    ])

    doc.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    buffer.seek(0)
    return buffer.getvalue()


def reset_filters() -> None:
    for key in list(st.session_state.keys()):
        if key.startswith("filter_"):
            st.session_state[key] = "Tous"


def reset_review_filters() -> None:
    for key in list(st.session_state.keys()):
        if key.startswith("review_filter_"):
            st.session_state[key] = "Tous"


def format_manifest_date(value: str | None) -> str:
    if not value:
        return "inconnue"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(value)




def status_palette(value: object, status_type: str) -> tuple[str, str]:
    val = str(value).strip() if pd.notna(value) else ""
    if status_type == "vigilance":
        mapping = {
            "Vigilance Critique": ("#D92D20", "#FFFFFF"),
            "Critique": ("#D92D20", "#FFFFFF"),
            "Vigilance Élevée": ("#F79009", "#FFFFFF"),
            "Élevée": ("#F79009", "#FFFFFF"),
            "Vigilance Modérée": ("#FEEFC6", "#8A4B00"),
            "Modérée": ("#FEEFC6", "#8A4B00"),
            "Vigilance Allégée": ("#D1FADF", "#065F46"),
            "Allégée": ("#D1FADF", "#065F46"),
            "Vigilance Aucune": ("#EAF2FB", "#163A59"),
            "Aucune": ("#EAF2FB", "#163A59"),
        }
        return mapping.get(val, ("#EEF2F7", "#334155"))
    mapping = {
        "Risque avéré": ("#D92D20", "#FFFFFF"),
        "Risque potentiel": ("#F79009", "#FFFFFF"),
        "Risque mitigé": ("#D1FADF", "#065F46"),
        "Risque levé": ("#E3F2E8", "#166534"),
        "Non calculable": ("#E5E7EB", "#475467"),
        "Aucun risque détecté": ("#EAF2FB", "#163A59"),
    }
    return mapping.get(val, ("#EEF2F7", "#334155"))


def render_status_badge(value: object, status_type: str) -> str:
    bg, fg = status_palette(value, status_type)
    return f'<span class="cm-badge" style="background:{bg}; color:{fg};">{escape(str(value))}</span>'


def render_small_table(
    df: pd.DataFrame,
    color_columns: dict[str, str] | None = None,
    *,
    bold_numbers: bool = True,
    scroll_x: bool = False,
) -> None:
    color_columns = color_columns or {}
    if df is None or df.empty:
        st.info("Aucune donnée à afficher.")
        return

    wrap_style = " style='overflow-x: auto; overflow-y: hidden;'" if scroll_x else ""
    html = [f"<div class='cm-mini-table-wrap'{wrap_style}><table class='cm-mini-table'><thead><tr>"]
    for col in df.columns:
        html.append(f"<th>{escape(str(col))}</th>")
    html.append("</tr></thead><tbody>")

    for _, row in df.iterrows():
        html.append("<tr>")
        for col in df.columns:
            value = row[col]
            classes = []
            if pd.api.types.is_number(value) and not isinstance(value, bool):
                classes.append("cm-number" if bold_numbers else "cm-number-soft")
            class_attr = f" class='{' '.join(classes)}'" if classes else ""
            if pd.isna(value):
                rendered = ""
            elif col in color_columns:
                status_type = color_columns[col]
                if status_type == "auto":
                    status_type = "vigilance" if str(value).strip().startswith("Vigilance") else "risk"
                rendered = render_status_badge(value, status_type)
            else:
                rendered = escape(str(value))
            html.append(f"<td{class_attr}>{rendered}</td>")
        html.append("</tr>")
    html.append("</tbody></table></div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_reference_table(
    df: pd.DataFrame,
    *,
    column_min_widths: list[str] | None = None,
) -> None:
    if df is None or df.empty:
        st.info("Aucune donnée à afficher.")
        return

    html = [
        "<div style='overflow-x: auto; overflow-y: hidden; background: rgba(255,255,255,0.8); border: 1px solid rgba(22, 58, 89, 0.12); border-radius: 18px; box-shadow: 0 10px 24px rgba(22, 58, 89, 0.06);'>",
        f"<table style='width: max-content; min-width: 100%; border-collapse: collapse; font-size: 0.94rem; table-layout: auto;'>",
    ]

    if column_min_widths:
        html.append("<colgroup>")
        for width in column_min_widths:
            html.append(f"<col style='min-width: {escape(str(width))};'>")
        html.append("</colgroup>")

    html.append("<thead><tr>")
    for col in df.columns:
        html.append(
            f"<th style='background: {PRIMARY_COLOR}; color: white; text-align: left; padding: 0.72rem 0.85rem; font-family: Sora, sans-serif; font-size: 0.8rem; font-weight: 700; letter-spacing: 0.04em; white-space: nowrap;'>{escape(str(col))}</th>"
        )
    html.append("</tr></thead><tbody>")

    for _, row in df.iterrows():
        html.append("<tr>")
        for value in row:
            rendered = "" if pd.isna(value) else escape(str(value)).replace("\n", "<br>")
            html.append(
                "<td style='padding: 0.72rem 0.85rem; border-top: 1px solid rgba(22, 58, 89, 0.08); vertical-align: top; color: #1F2937; text-align: left; white-space: normal;'>"
                + rendered
                + "</td>"
            )
        html.append("</tr>")
    html.append("</tbody></table></div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def dataframe_cell_style(value: object, status_type: str) -> str:
    if pd.isna(value):
        return ""
    bg, fg = status_palette(value, status_type)
    return f"background-color: {bg}; color: {fg}; font-weight: 700; border-radius: 999px;"


def style_dataframe(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = out[col].dt.strftime("%d/%m/%Y")
    styler = (
        out.style
        .hide(axis="index")
        .set_table_styles([
            {"selector": "th", "props": [("background-color", PRIMARY_COLOR), ("color", "white"), ("font-family", "Sora, sans-serif"), ("font-weight", "700")]},
            {"selector": "td", "props": [("border-color", "rgba(22, 58, 89, 0.08)")]},
        ])
    )
    if "Vigilance" in out.columns:
        styler = styler.map(lambda v: dataframe_cell_style(v, "vigilance"), subset=["Vigilance"])
    if "Risque" in out.columns:
        styler = styler.map(lambda v: dataframe_cell_style(v, "risk"), subset=["Risque"])
    if "Statut" in out.columns:
        styler = styler.map(lambda v: dataframe_cell_style(v, "risk"), subset=["Statut"])
    return styler


def render_admin_data_manager(user: dict) -> None:
    if user["role"] != "admin":
        return

    manifest = load_manifest()
    with st.sidebar.expander("Administration des données", expanded=False):
        if manifest:
            st.success(
                "Jeu actif : publié le {} par {}.".format(
                    format_manifest_date(manifest.get("published_at_utc")),
                    manifest.get("published_by_name") or manifest.get("published_by") or "inconnu",
                )
            )
            st.caption(
                "Sociétés : {} | Lignes 01/02/03 : {}/{}/{}".format(
                    manifest.get("societes_count", 0),
                    manifest.get("row_counts", {}).get("base", 0),
                    manifest.get("row_counts", {}).get("indicators", 0),
                    manifest.get("row_counts", {}).get("history", 0),
                )
            )
        else:
            st.warning("Aucun jeu de données publié pour le moment.")

        st.markdown("**Publier un nouveau jeu de données**")
        upload_base = st.file_uploader(
            "01_Donnees_base_source.csv",
            type=["csv"],
            key="admin_upload_base",
        )
        upload_indicators = st.file_uploader(
            "02_Indicateurs_source.csv",
            type=["csv"],
            key="admin_upload_indicators",
        )
        upload_history = st.file_uploader(
            "03_Indicateurs_historique.csv",
            type=["csv"],
            key="admin_upload_history",
        )

        if st.button("Publier ces 3 fichiers", type="primary", key="publish_dataset"):
            try:
                publish_uploaded_dataset(
                    {
                        "base": upload_base,
                        "indicators": upload_indicators,
                        "history": upload_history,
                    },
                    user,
                )
                st.success("Le nouveau jeu de données est maintenant actif pour tous les utilisateurs.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

        if manifest and st.button("Supprimer le jeu actif", type="secondary", key="clear_dataset"):
            clear_published_dataset()
            st.warning("Le jeu actif a été supprimé.")
            st.rerun()


def render_scope_selector(df: pd.DataFrame, user: dict):
    all_societies = available_societies(df)
    if user["role"] == "admin" or "ALL" in user["societes_autorisees"]:
        allowed = all_societies
    else:
        allowed = [s for s in all_societies if s in set(user["societes_autorisees"])]

    if not allowed:
        st.error("Votre compte ne possède aucun accès société correspondant aux données chargées.")
        st.stop()

    with st.sidebar:
        st.markdown("### Périmètre")
        selection = st.multiselect(
            "Sociétés visibles",
            options=allowed,
            default=allowed,
            key="selected_societies",
            help="Le tableau est calculé uniquement sur les sociétés sélectionnées parmi vos droits.",
        )

    if not selection:
        st.warning("Sélectionnez au moins une société pour afficher le tableau.")
        st.stop()

    return selection, allowed


def render_filters(df: pd.DataFrame) -> dict:
    st.subheader("Filtres")
    st.caption("Les filtres sont cumulatifs et recalculent tout le tableau.")

    if st.button("Réinitialiser les filtres", type="secondary"):
        reset_filters()

    row1 = st.columns(5)
    row2 = st.columns(4)
    labels = list(FILTER_MAPPING.keys())
    selections = {}

    for container, label in zip(row1 + row2, labels):
        column = FILTER_MAPPING[label]
        if column not in df.columns:
            options = ["Tous"]
        else:
            options = ["Tous"] + non_empty_sorted(df[column].unique())
        state_key = "filter_" + label
        if st.session_state.get(state_key) not in options:
            st.session_state[state_key] = "Tous"
        with container:
            selections[label] = st.selectbox(label, options=options, key=state_key)
    return selections


def render_kpis(df: pd.DataFrame) -> None:
    st.subheader("Bandeau de synthèse")
    client_level = build_unique_client_snapshot(
        df,
        [
            "Vigilance",
            "Risque",
            "Alerte justificatif incomplet",
            "Alerte sans prochaine revue",
            "Nb historique",
            "Vigilance Date de mise à jour",
        ],
    )
    total = len(client_level)
    vigilance_renforcee = int(client_level["Vigilance"].isin(CRITICAL_VIGILANCE).sum()) if "Vigilance" in client_level.columns else 0
    risque_avere = int((client_level["Risque"] == "Risque avéré").sum()) if "Risque" in client_level.columns else 0
    justificatifs_incomplets = int(client_level.get("Alerte justificatif incomplet", pd.Series(0, index=client_level.index)).fillna(0).sum())
    sans_revue = int(client_level.get("Alerte sans prochaine revue", pd.Series(0, index=client_level.index)).fillna(0).sum())
    historique_disponible = int(client_level.get("Nb historique", pd.Series(0, index=client_level.index)).fillna(0).gt(0).sum())

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Clients visibles", total)
    c2.metric("Vigilance renforcée", vigilance_renforcee)
    c3.metric("Risque avéré", risque_avere)
    c4.metric("Justificatifs incomplets", justificatifs_incomplets)
    c5.metric("Sans prochaine revue", sans_revue)
    c6.metric("Historique disponible", historique_disponible)

    if total and "Vigilance Date de mise à jour" in client_level.columns:
        last_update = client_level["Vigilance Date de mise à jour"].max()
        if pd.notna(last_update):
            st.caption("Fraîcheur visible : dernière mise à jour vigilance = {}.".format(last_update.strftime("%d/%m/%Y")))


def render_portfolio_glossary_expander() -> None:
    glossary_rows = [
        ["Segment", "Segment de rattachement du client dans le portefeuille."],
        ["Pays", "Pays de résidence du client."],
        ["Produit", "Produit(service) principal associé au client."],
        ["Canal", "Canal d’opérations principal observé sur 12 mois."],
        ["Vigilance", "Statut de vigilance du client."],
        ["Risque", "Statut de risque maximum du client."],
        ["EDD", "Statut EDD du dossier."],
        ["Analyste", "Analyste en charge du dossier."],
        ["Valideur", "Valideur du dossier."],
        ["Clients visibles", "Nombre de clients uniques visibles après application du périmètre société et des filtres."],
        ["Vigilance renforcée", "Clients dont la vigilance est 'Vigilance Élevée' ou 'Vigilance Critique'."],
        ["Risque avéré", "Clients dont le statut de risque est 'Risque avéré'."],
        ["Justificatifs incomplets", "Clients avec alerte de justificatif incomplet."],
        ["Sans prochaine revue", "Clients sans date de prochaine revue renseignée."],
        ["Historique disponible", "Clients avec au moins un historique disponible."],
        ["Fraîcheur visible", "Dernière date de mise à jour vigilance visible sur le portefeuille filtré."],
        ["Gouvernance", "Bloc de synthèse des alertes portefeuille."],
        ["Justificatif incomplet", "Alerte de complétude documentaire sur dossier renforcé."],
        ["Vigilance critique", "Alerte activée lorsque la vigilance du client est critique."],
        ["Revue trop ancienne", "Alerte activée quand la dernière revue dépasse le seuil métier prévu."],
        ["Cross-border élevé", "Alerte activée quand l’indicateur cross-border atteint un niveau élevé."],
        ["Cash intensité élevée", "Alerte activée quand le statut de cash intensité est jugé sensible."],
        ["% clients", "Poids du groupe dans le portefeuille filtré."],
        ["% de statut", "Poids du groupe dans le total d’un statut donné de vigilance ou de risque."],
        ["Dossiers prioritaires", "Top 10 des clients uniques classés par priorité décroissante."],
        ["Score priorité", "Score de classement des dossiers prioritaires, calculé à partir des vigilances, risques et alertes actives."],
        ["Motifs", "Liste textuelle des alertes actives expliquant la priorité du dossier."],
    ]

    calc_rows = [
        [
            "Segment (source)",
            "Champ 'Segment' lu directement dans le fichier 01 / base",
            "Client",
            "Utilisé tel quel dans les filtres et lectures de concentration de l’écran Portefeuille.",
        ],
        [
            "Pays (source)",
            "Champ 'Pays de résidence' lu directement dans le fichier 01 / base",
            "Client",
            "Le Top Pays et les concentrations Pays reposent sur cette colonne de base, pas sur le fichier 02 indicateurs.",
        ],
        [
            "Produit (source)",
            "Champ 'Produit(service) principal' lu directement dans le fichier 01 / base",
            "Client",
            "Le Top Produits et les concentrations Produits reposent sur cette colonne de base, pas sur le fichier 02 indicateurs.",
        ],
        [
            "Canal (source)",
            "Champ 'Canal d’opérations principal 12 mois' lu directement dans le fichier 01 / base",
            "Client",
            "Le Top Canaux et les concentrations Canaux reposent sur cette colonne de base, pas sur le fichier 02 indicateurs.",
        ],
        [
            "Clients visibles",
            "Nombre de clients uniques après déduplication par clé client",
            "Portefeuille filtré",
            "",
        ],
        [
            "Vigilance renforcée",
            "count(Vigilance ∈ {'Vigilance Élevée', 'Vigilance Critique'})",
            "Clients uniques",
            "",
        ],
        [
            "Risque avéré",
            "count(Risque == 'Risque avéré')",
            "Clients uniques",
            "",
        ],
        [
            "Justificatifs incomplets",
            "count(Alerte justificatif incomplet)",
            "Clients uniques",
            "L’alerte est calculée séparément ci-dessous.",
        ],
        [
            "Sans prochaine revue",
            "count(Alerte sans prochaine revue)",
            "Clients uniques",
            "",
        ],
        [
            "Historique disponible",
            "count(Nb historique > 0)",
            "Clients uniques",
            "",
        ],
        [
            "Fraîcheur visible",
            "max('Vigilance Date de mise à jour')",
            "Portefeuille filtré",
            "",
        ],
        [
            "Alerte justificatif incomplet",
            "(Flag justificatif complet != 'Oui') AND Vigilance ∈ {'Vigilance Élevée', 'Vigilance Critique'}",
            "Client",
            "",
        ],
        [
            "Alerte vigilance critique",
            "Vigilance == 'Vigilance Critique'",
            "Client",
            "",
        ],
        [
            "Alerte revue trop ancienne",
            "Vigilance renforcée AND Date dernière revue renseignée AND ancienneté > 90 jours",
            "Client",
            "",
        ],
        [
            "Alerte sans prochaine revue",
            "Date prochaine revue vide",
            "Client",
            "",
        ],
        [
            "Alerte cross-border élevé",
            "Cross border >= 0.25",
            "Client",
            "",
        ],
        [
            "Alerte cash intensité élevée",
            "Cash intensité Statut ∈ {'Risque potentiel', 'Risque avéré'}",
            "Client",
            "Affiché en Gouvernance, mais non utilisé dans le score priorité actuel.",
        ],
        [
            "% clients",
            "Nb clients du groupe / total clients du portefeuille filtré",
            "Groupe",
            "",
        ],
        [
            "% de statut en concentrations",
            "Nb clients du groupe dans le statut / total clients du portefeuille dans ce statut",
            "Groupe × statut",
            "S’applique aux statuts de vigilance et de risque.",
        ],
        [
            "Score priorité",
            "25×Vig. Critique + 15×Vig. Élevée + 20×Risq. avéré + 10×Risq. potentiel + "
            "12×Alerte justificatif incomplet + 8×Alerte vigilance critique + "
            "6×Alerte revue trop ancienne + 8×Alerte sans prochaine revue + "
            "5×Alerte cross-border élevé",
            "Client",
            "Utilisé pour classer les dossiers prioritaires.",
        ],
        [
            "Dossiers prioritaires",
            "Tri décroissant sur Score priorité, puis déduplication client, puis top 10",
            "Portefeuille filtré",
            "",
        ],
    ]

    with st.expander("Glossaire & calculs de l’écran Portefeuille", expanded=False):
        st.caption("Aide documentaire de lecture. Ce bloc n’a aucun impact sur le tableau affiché plus haut.")

        glossary_tab, calculation_tab = st.tabs(["Glossaire", "Calculs"])

        with glossary_tab:
            st.dataframe(
                pd.DataFrame(glossary_rows, columns=["Terme", "Définition"]),
                use_container_width=True,
                hide_index=True,
                height=520,
            )

        with calculation_tab:
            render_reference_table(
                pd.DataFrame(calc_rows, columns=["Indicateur", "Calcul / règle", "Périmètre", "Note"]),
                column_min_widths=["220px", "640px", "180px", "420px"],
            )





def render_analysis_glossary_expander() -> None:
    glossary_rows = [
        ["Indicateur", "Nom d’un indicateur d’alerte reconstruit à partir du fichier 02 et affiché ligne à ligne dans l’écran Analyse."],
        ["Statut indicateur", "Statut de risque porté par un indicateur : Risque avéré, Risque potentiel, Risque mitigé, Risque levé, Non calculable ou Sans risque."],
        ["Famille indicateur", "Famille de rattachement utilisée dans l’écran Analyse : Segment / Client, Indicateurs Pays, Indicateurs Produits, Indicateurs Canal."],
        ["Segment / Client", "Famille par défaut de l’écran Analyse. Elle regroupe tous les indicateurs qui ne relèvent pas des familles Pays, Produits ou Canal."],
        ["Indicateurs Pays", "Indicateurs classés comme géographiques ou juridictionnels, par exemple GAFI, UE, FR ou Bâle."],
        ["Indicateurs Produits", "Indicateurs rattachés à la nature du produit ou du service utilisé."],
        ["Indicateurs Canal", "Indicateurs rattachés au canal d’entrée en relation ou au mode d’opération."],
        ["Fraîcheur", "Ancienneté de la date de mise à jour d’un indicateur : < 30 jours, 30 à 90 jours, > 90 jours ou Sans date."],
        ["Clients concernés", "Nombre de clients uniques du portefeuille filtré ayant au moins un cas indicateur après application des filtres d’analyse."],
        ["Cas indicateurs", "Nombre total d’occurrences d’indicateurs visibles dans le périmètre filtré de l’écran Analyse."],
        ["Indicateurs distincts", "Nombre de libellés d’indicateurs différents présents dans le périmètre analysé."],
        ["Part du portefeuille filtré", "Part des clients concernés dans le portefeuille filtré courant."],
        ["Répartition", "Lecture des cas indicateurs par statut, par famille et par fraîcheur."],
        ["Top segment / client", "Bloc de concentration des indicateurs rattachés à la famille Segment / Client."],
        ["Top pays", "Bloc de concentration des indicateurs rattachés à la famille Indicateurs Pays."],
        ["Top produits", "Bloc de concentration des indicateurs rattachés à la famille Indicateurs Produits."],
        ["Top canaux", "Bloc de concentration des indicateurs rattachés à la famille Indicateurs Canal."],
        ["Indicateurs les plus contributifs", "Classement des indicateurs présentant le plus grand nombre total de cas sur le périmètre filtré."],
        ["Lecture détaillée des dimensions", "Table de drill-down permettant de partir d’une dimension et d’ouvrir les clients sous-jacents, sans modifier les calculs de Portefeuille."],
        ["Clients sous-jacents", "Liste opérationnelle des clients correspondant au focus sélectionné dans l’écran Analyse."],
    ]

    calc_rows = [
        [
            "Base de l’écran Analyse",
            "Normalisation du fichier 02 indicateurs en lignes [client × indicateur], puis jointure sur le portefeuille filtré pour récupérer Segment, Pays, Produit, Canal, Analyste, Valideur et les dates de revue.",
            "Cas indicateurs",
            "Les calculs Analyse sont isolés et n’impactent pas l’écran Portefeuille.",
        ],
        [
            "Cas indicateurs",
            "1 ligne par client × indicateur non vide issue du fichier 02 après normalisation",
            "Cas",
            "La vigilance est exclue de cette normalisation dédiée aux indicateurs d’alerte.",
        ],
        [
            "Clients concernés",
            "Nombre de clients uniques du scope Analyse filtré",
            "Clients uniques",
            "Construit à partir des clients ayant au moins un cas indicateur visible après filtres.",
        ],
        [
            "Cas indicateurs",
            "count(lignes de la base Analyse filtrée)",
            "Cas",
            "Chaque ligne correspond à une occurrence d’indicateur pour un client.",
        ],
        [
            "Indicateurs distincts",
            "nunique('Indicateur')",
            "Cas indicateurs",
            "Compte les libellés distincts visibles après filtres.",
        ],
        [
            "Part du portefeuille filtré",
            "Clients concernés / clients uniques du portefeuille filtré",
            "Portefeuille filtré",
            "Permet de mesurer le poids du scope Analyse dans le portefeuille courant.",
        ],
        [
            "Statuts du bandeau et de la répartition",
            "count(Statut == valeur) pour chacun des 6 statuts, puis % = cas du statut / total des cas visibles",
            "Cas",
            "L’étiquette UI 'Sans risque' correspond au statut source 'Aucun risque détecté'.",
        ],
        [
            "Famille indicateur",
            "Classification par correspondance exacte puis par mots-clés ; à défaut l’indicateur est rattaché à 'Segment / Client'",
            "Indicateur",
            "'SIREN / Catégorie juridique' et 'BODACC / Dépôt des comptes' sont forcés dans 'Segment / Client'.",
        ],
        [
            "Fraîcheur",
            "< 30 jours ; 30 à 90 jours ; > 90 jours ; Sans date, selon l’ancienneté de 'Date de mise à jour'",
            "Indicateur",
            "Calculée sur la date de mise à jour de chaque cas indicateur.",
        ],
        [
            "Top par famille",
            "Pour une famille donnée : regroupement par 'Indicateur', Nb = nombre de cas de la famille, % = Nb / total cas de la famille",
            "Famille × indicateur",
            "Les colonnes '% statut' mesurent le poids de l’indicateur dans le total du statut au sein de la famille.",
        ],
        [
            "Aperçu Top 3",
            "Affiche les 3 premiers indicateurs selon le tri actif dans la vue normale ; la vue agrandie expose le tableau complet",
            "Famille × indicateur",
            "Même logique de présentation que les tops de l’écran Portefeuille, adaptée à l’écran Analyse.",
        ],
        [
            "Indicateurs les plus contributifs",
            "Table croisée Indicateur × Statut, puis Total cas = somme des 6 statuts ; tri décroissant sur Total cas",
            "Indicateur",
            "Conserve la présentation actuelle du bloc de contribution.",
        ],
        [
            "Filtres Analyse",
            "Ligne 1 = filtres portefeuille ; ligne 2 = filtres indicateurs (Indicateur, Statut, Famille, Fraîcheur)",
            "Écran Analyse",
            "Les filtres Analyse ne modifient pas les résultats de l’écran Portefeuille.",
        ],
        [
            "Sources Segment / Pays / Produit / Canal",
            "Ces dimensions sont récupérées depuis le portefeuille joint à l’écran Analyse ; elles proviennent du fichier 01 / base via les champs Segment, Pays de résidence, Produit(service) principal et Canal d’opérations principal 12 mois.",
            "Client",
            "Les familles d’indicateurs, elles, sont déduites des libellés d’indicateurs du fichier 02.",
        ],
    ]

    with st.expander("Glossaire & calculs de l’écran Analyse", expanded=False):
        st.caption("Aide documentaire de lecture. Ce bloc n’a aucun impact sur les calculs de l’écran Portefeuille.")

        glossary_tab, calculation_tab = st.tabs(["Glossaire", "Calculs"])

        with glossary_tab:
            st.dataframe(
                pd.DataFrame(glossary_rows, columns=["Terme", "Définition"]),
                use_container_width=True,
                hide_index=True,
                height=520,
            )

        with calculation_tab:
            render_reference_table(
                pd.DataFrame(calc_rows, columns=["Indicateur", "Calcul / règle", "Périmètre", "Note"]),
                column_min_widths=["240px", "700px", "190px", "480px"],
            )




def render_distribution_block(title: str, dist_df: pd.DataFrame, index_col: str) -> None:
    st.markdown(f'<h3 class="cm-section-title">{escape(title)}</h3>', unsafe_allow_html=True)
    color_columns = {index_col: "vigilance"} if index_col == "Vigilance" else ({index_col: "risk"} if index_col == "Statut" else {})
    render_small_table(format_percent_column(dist_df), color_columns=color_columns)


def format_small_table_percent_columns(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    for col in output.columns:
        if str(col).startswith("%"):
            output[col] = output[col].map(lambda x: "" if pd.isna(x) else f"{float(x):.1%}".replace(".", ","))
    return output


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    color = str(hex_color or "").strip().lstrip("#")
    if len(color) != 6:
        return (22, 58, 89)
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _format_concentration_cell(value: object, column_name: str) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)) or pd.isna(value):
        return ""
    if isinstance(value, (int, float, np.number)) and str(column_name).startswith("%"):
        return f"{float(value):.1%}".replace(".", ",")
    return escape(str(value))


def concentration_cell_style(column_name: str, value: object, client_share: float) -> str:
    if column_name == "% clients":
        return "background:#EAF2FB; color:#163A59; font-weight:700;"
    if column_name not in CONCENTRATION_STATUS_STYLE:
        return ""
    try:
        status_share = float(value)
    except Exception:
        return ""
    if not np.isfinite(status_share):
        return ""
    delta = status_share - float(client_share or 0.0)
    if delta <= 0:
        return ""

    style_meta = CONCENTRATION_STATUS_STYLE[column_name]
    red, green, blue = _hex_to_rgb(style_meta["base"])
    intensity = min(delta / 0.20, 1.0)
    start_alpha = 0.08 + 0.14 * intensity
    end_alpha = 0.18 + 0.36 * intensity
    border_alpha = 0.14 + 0.30 * intensity
    return (
        f"background: linear-gradient(90deg, rgba({red}, {green}, {blue}, {start_alpha:.3f}), rgba({red}, {green}, {blue}, {end_alpha:.3f}));"
        f" color:{style_meta['text']}; font-weight:700;"
        f" box-shadow: inset 0 0 0 1px rgba({red}, {green}, {blue}, {border_alpha:.3f});"
    )


def _build_concentration_table_html(df: pd.DataFrame) -> str:
    html = ["<div class='cm-mini-table-wrap' style='overflow-x: auto; overflow-y: hidden;'><table class='cm-mini-table'><thead><tr>"]
    for col in df.columns:
        html.append(f"<th>{escape(str(col))}</th>")
    html.append("</tr></thead><tbody>")

    for _, row in df.iterrows():
        client_share = float(row.get("% clients", 0.0) or 0.0)
        html.append("<tr>")
        for col in df.columns:
            value = row[col]
            classes = []
            if pd.api.types.is_number(value) and not isinstance(value, bool):
                classes.append("cm-number")
            class_attr = f" class='{' '.join(classes)}'" if classes else ""
            style = concentration_cell_style(str(col), value, client_share)
            style_attr = f" style='{style}'" if style else ""
            rendered = _format_concentration_cell(value, str(col))
            html.append(f"<td{class_attr}{style_attr}>{rendered}</td>")
        html.append("</tr>")
    html.append("</tbody></table></div>")
    return "".join(html)


if hasattr(st, "dialog"):
    @st.dialog("Vue agrandie", width="large", icon=":material/open_in_full:")
    def show_concentration_top_dialog(title: str, df: pd.DataFrame) -> None:
        st.markdown(f'<div class="cm-subsection-title">{escape(title)}</div>', unsafe_allow_html=True)
        if df is None or df.empty:
            st.info("Aucune donnée à afficher.")
            return
        st.markdown(_build_concentration_table_html(df), unsafe_allow_html=True)
else:
    def show_concentration_top_dialog(title: str, df: pd.DataFrame) -> None:
        st.info("La vue agrandie nécessite une version plus récente de Streamlit prenant en charge st.dialog.")


def _build_concentration_top_preview_html(df: pd.DataFrame, sort_mode: str) -> str:
    if df is None or df.empty:
        return (
            "<div style='background:#FFFFFF;border:1px solid rgba(22,58,89,0.08);border-radius:18px;padding:14px 16px;box-shadow:0 12px 28px rgba(15,23,42,0.05);'>"
            "<div style='font-size:13px;color:#526273;'>Aucune donnée à afficher.</div>"
            "</div>"
        )

    label_column = str(df.columns[0]) if len(df.columns) else "Libellé"
    top_rows = df.head(3).copy()

    def metric_payload(row: dict[str, object]) -> tuple[str, object, str, str]:
        client_share = float(row.get("% clients", 0.0) or 0.0)
        normalized_sort = str(sort_mode or "% clients").strip().lower()
        if normalized_sort == "% vigilance":
            metric_columns = [col for col in CONCENTRATION_VIGILANCE_SORT_PRIORITY if col in top_rows.columns]
        elif normalized_sort == "% risque":
            metric_columns = [col for col in CONCENTRATION_RISK_SORT_PRIORITY if col in top_rows.columns]
        else:
            metric_columns = ["% clients"] if "% clients" in top_rows.columns else []

        if not metric_columns:
            return "", "", "", ""

        metric_col = metric_columns[0]
        if normalized_sort in {"% vigilance", "% risque"}:
            for candidate in metric_columns:
                value = row.get(candidate, 0.0)
                try:
                    value_float = float(value or 0.0)
                except Exception:
                    value_float = 0.0
                if value_float > 0:
                    metric_col = candidate
                    break

        metric_value = row.get(metric_col, "")
        metric_style = concentration_cell_style(metric_col, metric_value, client_share)
        metric_display = _format_concentration_cell(metric_value, metric_col)
        return metric_col, metric_value, metric_style, metric_display

    rows_html: list[str] = []
    for rank, row in enumerate(top_rows.to_dict('records'), start=1):
        label = escape(str(row.get(label_column, '')))
        metric_col, metric_raw, metric_style, metric_display = metric_payload(row)
        if metric_display:
            badge_label = escape(str(metric_col))
            badge_style = (metric_style or "") + " padding:4px 8px; border-radius:999px; white-space:nowrap; font-size:12px; font-weight:700;"
            metric_html = (
                f"<div style='display:flex;align-items:center;gap:6px;flex-wrap:wrap;justify-content:flex-end;'>"
                f"<div style='font-size:11px;color:#526273;white-space:nowrap;'>{badge_label}</div>"
                f"<div style='{badge_style}'>{metric_display}</div>"
                f"</div>"
            )
        else:
            metric_html = ""
        border_style = "border-bottom:1px solid rgba(22,58,89,0.08);" if rank < len(top_rows) else ""
        rows_html.append(
            f"<div style='display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding:9px 0;{border_style}'>"
            f"<div style='display:flex;align-items:flex-start;gap:10px;min-width:0;'>"
            f"<div style='min-width:22px;font-family:Sora,sans-serif;font-weight:800;font-size:13px;color:#163A59;'>{rank}.</div>"
            f"<div style='font-family:Sora,sans-serif;font-weight:700;font-size:14px;line-height:1.35;color:#163A59;word-break:break-word;'>{label}</div>"
            f"</div>"
            f"{metric_html}"
            f"</div>"
        )

    return (
        "<div style='background:#FFFFFF;border:1px solid rgba(22,58,89,0.08);border-radius:18px;padding:14px 16px;box-shadow:0 12px 28px rgba(15,23,42,0.05);'>"
        f"<div style='font-size:12px;color:#526273;margin-bottom:2px;'>Top 3 selon le tri <strong style='color:#163A59;'>{escape(str(sort_mode))}</strong>.</div>"
        + ''.join(rows_html)
        + "</div>"
    )


def render_top_block(title: str, df: pd.DataFrame, *, dialog_key: str | None = None, sort_mode: str = "% clients") -> None:
    title_col, action_col = st.columns([6.4, 0.8])
    with title_col:
        st.markdown(f'<h3 class="cm-section-title" style="white-space: nowrap; margin-bottom: 0;">{escape(title)}</h3>', unsafe_allow_html=True)
    with action_col:
        st.markdown("<div style='height: 0.10rem;'></div>", unsafe_allow_html=True)
        if dialog_key and st.button(
            " ",
            key=f"cm_expand_{dialog_key}",
            type="tertiary",
            icon=":material/open_in_full:",
            width="content",
            help="Ouvrir ce tableau dans une vue agrandie, sans modifier l'écran principal.",
        ):
            show_concentration_top_dialog(title, df)

    if df is None or df.empty:
        st.info("Aucune donnée à afficher.")
        return

    st.markdown(_build_concentration_top_preview_html(df, sort_mode), unsafe_allow_html=True)


def render_alert_block(title: str, df: pd.DataFrame) -> None:
    st.markdown(f'<h3 class="cm-section-title">{escape(title)}</h3>', unsafe_allow_html=True)
    render_small_table(df)




def display_value(value: object, kind: str | None = None) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)) or pd.isna(value):
        return "Non renseigné"
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return "Non renseigné"
        return value.strftime("%d/%m/%Y")
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return "Non renseigné"
    if kind == "percent":
        if isinstance(value, (int, float, np.number)):
            return f"{float(value):.1%}".replace(".", ",")
    return text


def sync_view_state_from_query_params() -> None:
    query_params = st.query_params
    view = str(query_params.get("view", "")).strip().lower()
    societe_id = str(query_params.get("societe", "")).strip()
    siren = str(query_params.get("siren", "")).strip()

    if view == "analyse":
        clear_ephemeral_state_if_view_changes("analysis")
        st.session_state["cm_view"] = "analysis"
    elif view in {"dates-revue", "dates_revue", "datesrevue", "planning"}:
        clear_ephemeral_state_if_view_changes("review_dates")
        st.session_state["cm_view"] = "review_dates"
    elif view in {"revues-simulations", "revues_simulations", "review-simulations", "review_simulations", "simulations"}:
        clear_ephemeral_state_if_view_changes("review_simulations")
        st.session_state["cm_view"] = "review_simulations"
    elif view in {"evolution", "évolution"}:
        clear_ephemeral_state_if_view_changes("evolution")
        st.session_state["cm_view"] = "evolution"

    if view == "client" and societe_id and siren:
        clear_ephemeral_state_if_view_changes("client")
        st.session_state["cm_view"] = "client"
        st.session_state["cm_client_societe"] = societe_id
        st.session_state["cm_client_siren"] = siren


def siren_society_column(df: pd.DataFrame) -> str | None:
    if df is None or df.empty:
        return None
    if SOC_COL in df.columns:
        return SOC_COL
    if "Société" in df.columns:
        return "Société"
    if "__societe_id" in df.columns:
        return "__societe_id"
    return None


def reorder_table_columns_for_ui(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    columns = list(df.columns)
    preferred: list[str] = []
    for candidate in ["SIREN", "Dénomination", "Client", "Vigilance", "Risque", SOC_COL, "Société"]:
        if candidate in columns and candidate not in preferred:
            preferred.append(candidate)

    remaining = [col for col in columns if col not in preferred]
    return df[preferred + remaining]


def table_column_weight(column_name: str) -> float:
    if column_name in {"SIREN", "#", "Rang", "Nb", "%"}:
        return 0.95
    if column_name in {"Dénomination", "Client"}:
        return 1.8
    if column_name in {"Vigilance", "Risque", SOC_COL, "Société", "Statut EDD", "EDD"}:
        return 1.25
    if column_name in {"Motifs", "Commentaire"}:
        return 2.25
    return 1.1



def status_emoji(value: object, palette: str = "generic") -> str:
    text = display_value(value)
    lower = text.lower()
    if text == "-":
        return "⚪"
    if palette == "vigilance":
        if "critique" in lower:
            return "🔴"
        if "élev" in lower:
            return "🟠"
        if "modér" in lower:
            return "🟡"
        if "allég" in lower:
            return "🟢"
        if "aucune" in lower:
            return "🟢"
    if palette == "risk":
        if "avéré" in lower or "critique" in lower:
            return "🔴"
        if "élev" in lower or "fort" in lower:
            return "🟠"
        if "modér" in lower or "surveillance" in lower:
            return "🟡"
        if any(token in lower for token in ["faible", "levé", "aucun", "mitig", "clos", "normal"]):
            return "🟢"
    return "🔵"


def format_table_display_dataframe(df: pd.DataFrame, preserve_order: bool = False) -> pd.DataFrame:
    display_df = df.copy() if preserve_order else reorder_table_columns_for_ui(df.copy())
    visible_columns = [col for col in display_df.columns if not str(col).startswith("__")]
    display_df = display_df[visible_columns].copy()
    for col in display_df.columns:
        series = display_df[col]
        if pd.api.types.is_datetime64_any_dtype(series):
            display_df[col] = pd.to_datetime(series, errors="coerce").dt.strftime("%d/%m/%Y").fillna("")
            continue
        if col.startswith("%") or "%" in col:
            display_df[col] = series.map(lambda x: "" if pd.isna(x) else f"{float(x) * 100:.1f} %".replace('.', ','))
            continue
        if col == "SIREN":
            display_df[col] = series.apply(lambda x: f"↗ {display_value(x)}")
            continue
        if col == "Vigilance":
            display_df[col] = series.apply(lambda x: f"{status_emoji(x, 'vigilance')} {display_value(x)}")
            continue
        if col in {"Risque", "Statut"}:
            display_df[col] = series.apply(lambda x: f"{status_emoji(x, 'risk')} {display_value(x)}")
            continue
        if pd.api.types.is_numeric_dtype(series):
            non_null = series.dropna()
            if non_null.empty:
                display_df[col] = series.map(lambda x: "" if pd.isna(x) else str(x))
            elif np.allclose(non_null.astype(float) % 1, 0):
                display_df[col] = series.map(lambda x: "" if pd.isna(x) else f"{int(round(float(x))):,}".replace(",", " "))
            else:
                display_df[col] = series.map(lambda x: "" if pd.isna(x) else f"{float(x):,.1f}".replace(",", " ").replace(".", ","))
            continue
        display_df[col] = series.apply(display_value)
    return display_df


def style_interactive_table(display_df: pd.DataFrame, raw_df: pd.DataFrame) -> pd.io.formats.style.Styler:
    def style_cell(column_name: str, value: object) -> str:
        base = "padding: 0.42rem 0.55rem; text-align: center; vertical-align: middle; border-bottom: 1px solid rgba(22,58,89,0.08);"
        text = str(value)
        if column_name == "SIREN":
            return base + "color: #163A59; font-weight: 800; text-decoration: underline;"
        if column_name in {"Dénomination", "Client"}:
            return base + "text-align: center; font-weight: 700; color: #163A59;"
        if column_name == "Vigilance":
            if "🔴" in text:
                return base + "background-color: rgba(191, 36, 36, 0.10); color: #8A1F1F; font-weight: 700; border-radius: 999px;"
            if "🟠" in text:
                return base + "background-color: rgba(209, 98, 0, 0.10); color: #9A4D00; font-weight: 700; border-radius: 999px;"
            if "🟡" in text:
                return base + "background-color: rgba(184, 134, 11, 0.12); color: #7A5A00; font-weight: 700; border-radius: 999px;"
            if "🟢" in text:
                return base + "background-color: rgba(31, 122, 74, 0.10); color: #1F7A4A; font-weight: 700; border-radius: 999px;"
        if column_name in {"Risque", "Statut"}:
            if "🔴" in text:
                return base + "background-color: rgba(191, 36, 36, 0.10); color: #8A1F1F; font-weight: 700; border-radius: 999px;"
            if "🟠" in text:
                return base + "background-color: rgba(209, 98, 0, 0.10); color: #9A4D00; font-weight: 700; border-radius: 999px;"
            if "🟡" in text:
                return base + "background-color: rgba(184, 134, 11, 0.12); color: #7A5A00; font-weight: 700; border-radius: 999px;"
            if "🟢" in text:
                return base + "background-color: rgba(31, 122, 74, 0.10); color: #1F7A4A; font-weight: 700; border-radius: 999px;"
        if column_name.startswith("%") or "%" in column_name:
            return base + "font-variant-numeric: tabular-nums; font-weight: 700;"
        if column_name in {"Clients", "Vigilances critiques", "Risques avérés", "Nb", "#", "Rang", "Score", "Score priorité"}:
            return base + "font-variant-numeric: tabular-nums; font-weight: 700;"
        return base

    zebra = pd.DataFrame("", index=display_df.index, columns=display_df.columns)
    zebra.iloc[1::2, :] = "background-color: rgba(22,58,89,0.025);"

    styled = display_df.style
    styled = styled.set_table_styles([
        {"selector": "thead th", "props": [("background-color", "#163A59"), ("color", "white"), ("font-weight", "700"), ("text-transform", "uppercase"), ("font-size", "0.76rem"), ("letter-spacing", "0.08em"), ("text-align", "center"), ("border-bottom", "0")]},
        {"selector": "thead th.col_heading.level0", "props": [("background-color", "#163A59"), ("color", "white"), ("text-align", "center")]},
        {"selector": "thead tr", "props": [("background-color", "#163A59")]},
        {"selector": "tbody td", "props": [("background-color", "#ffffff"), ("text-align", "center")]},
    ])
    styled = styled.apply(lambda _: zebra, axis=None)
    styled = styled.apply(lambda s: [style_cell(s.name, v) for v in s], axis=0)
    return styled



def render_clickable_streamlit_table(
    df: pd.DataFrame,
    *,
    height: int | None = None,
    key_prefix: str = "table",
    preserve_order: bool = False,
    auto_size_columns: bool = False,
    pinned_columns: list[str] | None = None,
    table_width: str = "stretch",
    column_width_overrides: dict[str, str | None] | None = None,
) -> None:
    if df is None or df.empty:
        st.info("Aucune donnée disponible.")
        return

    raw_df = (df.copy() if preserve_order else reorder_table_columns_for_ui(df.copy())).reset_index(drop=True)
    if len(raw_df) > 300:
        st.caption("Aperçu limité aux 300 premières lignes pour conserver une navigation fluide.")
        raw_df = raw_df.head(300).copy().reset_index(drop=True)

    display_df = format_table_display_dataframe(raw_df, preserve_order=preserve_order)
    society_col = siren_society_column(raw_df)
    pinned_set = {str(col) for col in (pinned_columns or [])}
    width_overrides = {str(col): width for col, width in (column_width_overrides or {}).items()}

    if "SIREN" in raw_df.columns and society_col is not None:
        st.markdown(
            "<div class='cm-stream-note'><strong>↗ Cliquez directement sur une cellule de la colonne SIREN</strong> pour ouvrir la fiche client.</div>",
            unsafe_allow_html=True,
        )

    def _text_column(
        label: str,
        *,
        width: str | None = None,
        help: str | None = None,
        pinned: bool = False,
    ) -> object:
        kwargs: dict[str, object] = {}
        if width is not None:
            kwargs["width"] = width
        if help is not None:
            kwargs["help"] = help
        if pinned:
            kwargs["pinned"] = True
        try:
            return st.column_config.TextColumn(label, **kwargs)
        except TypeError:
            kwargs.pop("pinned", None)
            return st.column_config.TextColumn(label, **kwargs)

    column_config: dict[str, object] = {}
    for col in display_df.columns:
        is_pinned = str(col) in pinned_set
        forced_width = width_overrides.get(str(col))
        if forced_width is not None:
            column_config[col] = _text_column("SIREN" if col == "SIREN" else col, width=forced_width, pinned=is_pinned)
        elif auto_size_columns:
            column_config[col] = _text_column(col, pinned=is_pinned)
        elif col == "SIREN":
            column_config[col] = _text_column("SIREN", width="small", pinned=is_pinned)
        elif col in {"Dénomination", "Client"}:
            column_config[col] = _text_column(col, width="large", pinned=is_pinned)
        elif col in {"Vigilance", "Risque", "Statut", SOC_COL, "Société"}:
            column_config[col] = _text_column(col, width="medium", pinned=is_pinned)
        elif col in {"Nb", "%", "#", "Rang", "Score", "Score priorité"}:
            column_config[col] = _text_column(col, width="small", pinned=is_pinned)
        else:
            column_config[col] = _text_column(col, width="medium", pinned=is_pinned)

    event = st.dataframe(
        style_interactive_table(display_df, raw_df),
        width=table_width,
        height=height if height is not None else "auto",
        hide_index=True,
        column_order=list(display_df.columns),
        column_config=column_config,
        on_select="rerun",
        selection_mode="single-cell",
        row_height=40,
        key=f"cm_df_{key_prefix}",
    )

    cells = []
    if event is not None:
        try:
            cells = list(event.selection.get("cells", []))
        except Exception:
            cells = []

    if cells and society_col is not None and "SIREN" in raw_df.columns:
        row_idx, col_name = cells[0]
        if col_name == "SIREN" and 0 <= int(row_idx) < len(raw_df):
            row = raw_df.iloc[int(row_idx)]
            open_client_detail(str(row.get(society_col, "")), str(row.get("SIREN", "")))
            st.rerun()


def render_clickable_dataframe(
    df: pd.DataFrame,
    *,
    use_container_width: bool = True,
    height: int | None = None,
    hide_index: bool = True,
    key_prefix: str = "table",
    preserve_order: bool = False,
    auto_size_columns: bool = False,
    pinned_columns: list[str] | None = None,
    table_width: str = "stretch",
    column_width_overrides: dict[str, str | None] | None = None,
) -> None:
    render_clickable_streamlit_table(
        df,
        height=height,
        key_prefix=key_prefix,
        preserve_order=preserve_order,
        auto_size_columns=auto_size_columns,
        pinned_columns=pinned_columns,
        table_width=table_width,
        column_width_overrides=column_width_overrides,
    )


def render_clickable_styled_dataframe(
    styler: pd.io.formats.style.Styler,
    source_df: pd.DataFrame,
    *,
    use_container_width: bool = True,
    height: int | None = None,
    hide_index: bool = True,
    key_prefix: str = "table",
    preserve_order: bool = False,
    auto_size_columns: bool = False,
    pinned_columns: list[str] | None = None,
    table_width: str = "stretch",
    column_width_overrides: dict[str, str | None] | None = None,
) -> None:
    render_clickable_streamlit_table(
        source_df,
        height=height,
        key_prefix=key_prefix,
        preserve_order=preserve_order,
        auto_size_columns=auto_size_columns,
        pinned_columns=pinned_columns,
        table_width=table_width,
        column_width_overrides=column_width_overrides,
    )


def client_label(row: pd.Series) -> str:
    return f"{row.get('Dénomination', 'Client')} · {row.get('SIREN', '')} · {row.get(SOC_COL, '')}"


def open_client_detail(societe_id: str, siren: str) -> None:
    current_view = st.session_state.get("cm_view", "portfolio")
    if current_view == "client":
        current_view = st.session_state.get("cm_previous_view", "portfolio")
    clear_ephemeral_state_if_view_changes("client")
    st.session_state["cm_previous_view"] = current_view or "portfolio"
    st.session_state["cm_view"] = "client"
    st.session_state["cm_client_societe"] = societe_id
    st.session_state["cm_client_siren"] = siren


def return_from_client() -> None:
    target_view = st.session_state.get("cm_previous_view", "portfolio") or "portfolio"
    clear_ephemeral_state_if_view_changes(str(target_view))
    st.session_state["cm_view"] = target_view
    st.session_state.pop("cm_client_societe", None)
    st.session_state.pop("cm_client_siren", None)
    st.query_params.clear()


def render_client_launcher(df: pd.DataFrame, key_prefix: str = "portfolio") -> None:
    clients = (
        df[[SOC_COL, "SIREN", "Dénomination"]]
        .drop_duplicates()
        .sort_values(["Dénomination", SOC_COL, "SIREN"], na_position="last")
        .reset_index(drop=True)
    )
    if clients.empty:
        return

    labels = clients.apply(client_label, axis=1).tolist()
    st.markdown('<h3 class="cm-section-title">Accès direct à la fiche client</h3>', unsafe_allow_html=True)
    col_a, col_b = st.columns([5, 1])
    with col_a:
        selected_label = st.selectbox(
            "Choisir un client",
            options=labels,
            key=f"{key_prefix}_client_selector",
            help="Recherchez un client par dénomination, SIREN ou société puis ouvrez sa fiche détaillée.",
        )
    with col_b:
        st.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
        if st.button("Ouvrir", type="primary", key=f"{key_prefix}_open_client_btn"):
            row = clients.loc[labels.index(selected_label)]
            open_client_detail(str(row[SOC_COL]), str(row["SIREN"]))
            st.rerun()


INDICATOR_SUFFIXES = [
    ("Date de dernière mise à jour", "Date de mise à jour"),
    ("Date de mise à jour", "Date de mise à jour"),
    ("Date de création", "Date de création"),
    ("Référence dossier source", "Référence du dossier source"),
    ("Pièce associée", "Pièce associée"),
    ("Justificatif", "Justificatif"),
    ("Commentaire", "Commentaire"),
    ("Analyste", "Analyste"),
    ("Valideur", "Valideur"),
    ("Valeur", "Valeur"),
    ("valeur", "Valeur"),
    ("Statut", "Statut"),
    ("statut", "Statut"),
]


def indicator_group_map(columns: list[str]) -> dict[str, dict[str, str]]:
    groups: dict[str, dict[str, str]] = {}
    for raw_col in columns:
        col = " ".join(str(raw_col).replace("\ufeff", "").split())
        if col in {SOC_COL, "SIREN", "Dénomination"}:
            continue
        for suffix, field_name in INDICATOR_SUFFIXES:
            if col.endswith(suffix):
                indicator_name = col[: -len(suffix)].strip()
                if indicator_name:
                    groups.setdefault(indicator_name, {})[field_name] = raw_col
                break
    return groups


def build_indicator_table_from_series(row: pd.Series) -> pd.DataFrame:
    groups = indicator_group_map(list(row.index))
    output_rows = []
    for indicator_name, mapping in groups.items():
        item = {
            "Indicateur": indicator_name,
            "Valeur": row.get(mapping.get("Valeur"), pd.NA),
            "Statut": row.get(mapping.get("Statut"), pd.NA),
            "Date de création": row.get(mapping.get("Date de création"), pd.NA),
            "Date de mise à jour": row.get(mapping.get("Date de mise à jour"), pd.NA),
            "Commentaire": row.get(mapping.get("Commentaire"), pd.NA),
            "Justificatif": row.get(mapping.get("Justificatif"), pd.NA),
            "Analyste": row.get(mapping.get("Analyste"), pd.NA),
            "Valideur": row.get(mapping.get("Valideur"), pd.NA),
            "Pièce associée": row.get(mapping.get("Pièce associée"), pd.NA),
            "Référence du dossier source": row.get(mapping.get("Référence du dossier source"), pd.NA),
        }
        non_key_values = [item[k] for k in item if k != "Indicateur"]
        if all(pd.isna(v) or not str(v).strip() for v in non_key_values):
            continue
        output_rows.append(item)

    table = pd.DataFrame(output_rows)
    if table.empty:
        return table

    for date_col in ["Date de création", "Date de mise à jour"]:
        table[date_col] = pd.to_datetime(table[date_col], errors="coerce")

    table = table.sort_values(["Date de mise à jour", "Indicateur"], ascending=[False, True], na_position="last")
    return table.reset_index(drop=True)


def render_info_cards(items: list[tuple[str, object, str | None]]) -> None:
    html = ["<div class='cm-client-grid'>"]
    for label, value, kind in items:
        html.append(
            "<div class='cm-client-field'>"
            f"<div class='cm-client-field-label'>{escape(str(label))}</div>"
            f"<div class='cm-client-field-value'>{escape(display_value(value, kind))}</div>"
            "</div>"
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_indicator_table(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("Aucun indicateur disponible pour ce client.")
        return

    formatted = df.copy()
    for date_col in ["Date de création", "Date de mise à jour"]:
        if date_col in formatted.columns:
            formatted[date_col] = formatted[date_col].apply(display_value)
    for col in formatted.columns:
        if col not in {"Indicateur", "Valeur", "Statut"}:
            formatted[col] = formatted[col].apply(lambda v: display_value(v))
    render_small_table(formatted, color_columns={"Statut": "auto"})


def render_client_header(client_row: pd.Series) -> None:
    st.markdown('<div class="cm-client-breadcrumb">Portefeuille &gt; Client &gt; Fiche client</div>', unsafe_allow_html=True)
    header_cards = [
        ("Date calcul du risque", client_row.get("Date calcul du risque"), None),
        ("Dernière mise à jour vigilance", client_row.get("Vigilance Date de mise à jour"), None),
        ("Dernière revue", client_row.get("Date dernière revue"), None),
        ("Prochaine revue", client_row.get("Date prochaine revue"), None),
    ]
    badges = [
        render_status_badge(display_value(client_row.get("Vigilance")), "vigilance"),
        render_status_badge(display_value(client_row.get("Risque")), "risk"),
        render_status_badge(display_value(client_row.get("Statut EDD")), "edd"),
    ]
    cards_html = []
    for label, value, kind in header_cards:
        cards_html.append(
            "<div class='cm-client-hero-card'>"
            f"<div class='cm-client-hero-label'>{escape(label)}</div>"
            f"<div class='cm-client-hero-value'>{escape(display_value(value, kind))}</div>"
            "</div>"
        )
    st.markdown(
        "<div class='cm-client-hero'>"
        "<div class='cm-client-title-row'>"
        "<div>"
        f"<div class='cm-client-title'>{escape(display_value(client_row.get('Dénomination')))}</div>"
        f"<div class='cm-client-subtitle'>SIREN : {escape(display_value(client_row.get('SIREN')))} · Société : {escape(display_value(client_row.get(SOC_COL)))}</div>"
        "</div>"
        "</div>"
        f"<div class='cm-client-badges'>{''.join(badges)}</div>"
        f"<div class='cm-client-hero-grid'>{''.join(cards_html)}</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_client_base_tab(client_row: pd.Series) -> None:
    base_items = [
        ("Identifiant client / SIREN", client_row.get("SIREN"), None),
        ("Dénomination", client_row.get("Dénomination"), None),
        ("Segment", client_row.get("Segment"), None),
        ("Pays de résidence", client_row.get("Pays de résidence"), None),
        ("Produit principal", client_row.get("Produit(service) principal"), None),
        ("Canal principal", client_row.get("Canal d’opérations principal 12 mois"), None),
        ("Score importé", client_row.get("Vigilance valeur"), "percent"),
        ("Niveau de vigilance", client_row.get("Vigilance"), None),
        ("Statut de risque", client_row.get("Risque"), None),
        ("Date calcul du risque", client_row.get("Date calcul du risque"), None),
        ("Date et heure de synchronisation", client_row.get("Vigilance Date de mise à jour"), None),
        ("Identifiant / référence source", client_row.get("Référence du dossier source"), None),
        ("Code NAF", client_row.get("Code NAF (nomenclature INSEE)"), None),
        ("Catégorie juridique", client_row.get("Catégorie Juridique"), None),
        ("Nationalité", client_row.get("Nationalité"), None),
        ("Canal onboarding", client_row.get("Canal distribution On boarding"), None),
        ("Cross border", client_row.get("Cross border"), "percent"),
        ("Cash intensité", client_row.get("Cash intensité"), "percent"),
        ("Analyste", client_row.get("Analyste"), None),
        ("Valideur", client_row.get("Valideur"), None),
        ("Date dernière revue", client_row.get("Date dernière revue"), None),
        ("Date prochaine revue", client_row.get("Date prochaine revue"), None),
        ("Justificatif complet", client_row.get("Flag justificatif complet"), None),
    ]
    render_info_cards(base_items)


def apply_indicator_local_filters(df: pd.DataFrame, key_prefix: str) -> pd.DataFrame:
    if df.empty:
        return df
    c1, c2, c3 = st.columns(3)
    statuses = ["Tous"] + non_empty_sorted(df["Statut"].dropna().unique()) if "Statut" in df.columns else ["Tous"]
    with c1:
        selected_status = st.selectbox("Statut", statuses, key=f"{key_prefix}_status")
    with c2:
        comment_filter = st.selectbox(
            "Commentaire",
            ["Tous", "Avec commentaire", "Sans commentaire"],
            key=f"{key_prefix}_comment",
        )
    with c3:
        evidence_filter = st.selectbox(
            "Justificatif",
            ["Tous", "Avec justificatif", "Sans justificatif"],
            key=f"{key_prefix}_evidence",
        )

    filtered = df.copy()
    if selected_status != "Tous":
        filtered = filtered[filtered["Statut"] == selected_status]
    if comment_filter == "Avec commentaire":
        filtered = filtered[filtered["Commentaire"].astype(str).str.strip().ne("") & filtered["Commentaire"].notna()]
    elif comment_filter == "Sans commentaire":
        filtered = filtered[filtered["Commentaire"].isna() | filtered["Commentaire"].astype(str).str.strip().eq("")]
    if evidence_filter == "Avec justificatif":
        filtered = filtered[filtered["Justificatif"].astype(str).str.strip().ne("") & filtered["Justificatif"].notna()]
    elif evidence_filter == "Sans justificatif":
        filtered = filtered[filtered["Justificatif"].isna() | filtered["Justificatif"].astype(str).str.strip().eq("")]
    return filtered.reset_index(drop=True)


def render_client_indicators_tab(indicators_row: pd.Series) -> None:
    indicator_table = build_indicator_table_from_series(indicators_row)
    indicator_table = apply_indicator_local_filters(indicator_table, "client_current_indicators")
    render_indicator_table(indicator_table)
    if not indicator_table.empty:
        st.download_button(
            label="Exporter les indicateurs courants (.csv)",
            data=dataframe_to_csv_bytes(indicator_table),
            file_name="fiche_client_indicateurs.csv",
            mime="text/csv",
            type="secondary",
            key="export_current_indicators",
        )


def render_client_history_tab(history_rows: pd.DataFrame) -> None:
    if history_rows.empty:
        st.info("Aucun état historique n'est disponible pour ce client.")
        return

    rows = history_rows.copy()
    date_cols = [c for c in rows.columns if "Date de mise à jour" in c]
    if date_cols:
        for col in date_cols:
            rows[col] = pd.to_datetime(rows[col], errors="coerce")
        rows["_latest_history_date"] = rows[date_cols].max(axis=1)
        rows = rows.sort_values("_latest_history_date", ascending=False, na_position="last").drop(columns=["_latest_history_date"])
    else:
        rows = rows.copy()

    st.caption("Les états antérieurs sont présentés séparément, du plus récent au plus ancien, avec la même structure que l'état courant.")
    for idx, (_, hist_row) in enumerate(rows.iterrows(), start=1):
        hist_table = build_indicator_table_from_series(hist_row)
        if hist_table.empty:
            continue
        latest = hist_table["Date de mise à jour"].max() if "Date de mise à jour" in hist_table.columns else pd.NaT
        suffix = f" · dernière mise à jour max {display_value(latest)}" if pd.notna(latest) else ""
        with st.expander(f"État historique {idx}{suffix}", expanded=(idx == 1)):
            render_indicator_table(hist_table)


def render_client_edd_tab(client_row: pd.Series, history_rows: pd.DataFrame) -> None:
    left, right = st.columns([1.3, 1.0])
    with left:
        st.markdown('<h3 class="cm-section-title">EDD courant</h3>', unsafe_allow_html=True)
        edd_items = [
            ("Statut EDD", client_row.get("Statut EDD"), None),
            ("Analyste", client_row.get("Analyste"), None),
            ("Valideur", client_row.get("Valideur"), None),
            ("Date dernière revue", client_row.get("Date dernière revue"), None),
            ("Date prochaine revue", client_row.get("Date prochaine revue"), None),
            ("Justificatif complet", client_row.get("Flag justificatif complet"), None),
            ("Conclusion synthétique", client_row.get("Motifs"), None),
        ]
        render_info_cards(edd_items)
    with right:
        st.markdown('<h3 class="cm-section-title">Pilotage synthétique</h3>', unsafe_allow_html=True)
        pilotage = pd.DataFrame(
            [
                ["Score priorité", display_value(client_row.get("Score priorité"))],
                ["Nb historique", display_value(client_row.get("Nb historique"))],
                ["Nb risque avéré", display_value(client_row.get("Nb Risque avéré"))],
                ["Nb risque potentiel", display_value(client_row.get("Nb Risque potentiel"))],
                ["Nb risque mitigé", display_value(client_row.get("Nb Risque mitigé"))],
                ["Nb risque levé", display_value(client_row.get("Nb Risque levé"))],
                ["Nb non calculable", display_value(client_row.get("Nb Non calculable"))],
                ["Motifs / alertes", display_value(client_row.get("Motifs"))],
            ],
            columns=["Indicateur", "Valeur"],
        )
        render_small_table(pilotage)

    st.markdown('<h3 class="cm-section-title">Historique des validations et audit trail</h3>', unsafe_allow_html=True)
    if history_rows.empty:
        st.markdown(
            "<div class='cm-empty-note'>Le jeu 01 / 02 / 03 publié ne contient pas de journal d'événements de gouvernance distinct. "
            "Cette zone affichera l'audit trail consolidé dès qu'un flux dédié sera disponible.</div>",
            unsafe_allow_html=True,
        )
    else:
        latest_dates = []
        date_cols = [c for c in history_rows.columns if "Date de mise à jour" in c]
        if date_cols:
            tmp = history_rows.copy()
            for col in date_cols:
                tmp[col] = pd.to_datetime(tmp[col], errors="coerce")
            latest_dates = tmp[date_cols].max(axis=1).sort_values(ascending=False).tolist()
        audit_rows = pd.DataFrame(
            [
                ["Historique indicateurs disponible", len(history_rows)],
                ["Dernier état historique le plus récent", display_value(latest_dates[0]) if latest_dates else "Non renseigné"],
                ["Observation", "Le flux publié ne fournit pas encore le détail des validations, actions, motifs et justificatifs de gouvernance."],
            ],
            columns=["Élément", "Valeur"],
        )
        render_small_table(audit_rows)


def render_client_screen(
    portfolio: pd.DataFrame,
    indicators: pd.DataFrame,
    history: pd.DataFrame,
    selected_societies: list[str],
    allowed_societies: list[str],
) -> None:
    societe_id = st.session_state.get("cm_client_societe")
    siren = st.session_state.get("cm_client_siren")
    if not societe_id or not siren:
        return_from_client()
        st.rerun()

    allowed_set = {str(s).strip().upper() for s in allowed_societies}
    if str(societe_id).strip().upper() not in allowed_set:
        st.error("Cette fiche client n'appartient pas à votre périmètre autorisé.")
        if st.button("Retour", key="btn_back_unauthorized"):
            return_from_client()
            st.rerun()
        return

    client_rows = portfolio[(portfolio[SOC_COL] == societe_id) & (portfolio["SIREN"] == siren)]
    if client_rows.empty:
        st.warning("Le client demandé n'est plus disponible dans le jeu actif.")
        if st.button("Retour", key="btn_back_missing"):
            return_from_client()
            st.rerun()
        return

    client_row = client_rows.iloc[0]
    indicator_rows = indicators[(indicators[SOC_COL] == societe_id) & (indicators["SIREN"] == siren)]
    history_rows = history[(history[SOC_COL] == societe_id) & (history["SIREN"] == siren)]

    top_left, top_right = st.columns([6, 1])
    with top_left:
        render_client_header(client_row)
    with top_right:
        st.markdown("<div style='height: 0.3rem'></div>", unsafe_allow_html=True)
        if st.button("← Retour", type="secondary", key="back_to_portfolio_top"):
            return_from_client()
            st.rerun()

    tabs = st.tabs(["Données de base", "Indicateurs", "Historique des indicateurs", "EDD et historique"])
    with tabs[0]:
        render_client_base_tab(client_row)
    with tabs[1]:
        if indicator_rows.empty:
            st.info("Aucun indicateur courant n'est disponible pour ce client.")
        else:
            render_client_indicators_tab(indicator_rows.iloc[0])
    with tabs[2]:
        render_client_history_tab(history_rows)
    with tabs[3]:
        render_client_edd_tab(client_row, history_rows)



def render_primary_navigation(current_view: str) -> str:
    label_map = {
        "portfolio": "Portefeuille",
        "analysis": "Analyse",
        "review_dates": "Planification des revues",
        "review_simulations": "Revues & Simulations",
        "evolution": "Évolution",
    }
    options = ["Portefeuille", "Analyse", "Planification des revues", "Revues & Simulations", "Évolution"]
    current_label = label_map.get(current_view, "Portefeuille")
    selection = st.radio(
        "Navigation principale",
        options=options,
        horizontal=True,
        label_visibility="collapsed",
        index=options.index(current_label),
        key="cm_main_nav_radio",
    )
    if selection == "Analyse":
        return "analysis"
    if selection == "Planification des revues":
        return "review_dates"
    if selection == "Revues & Simulations":
        return "review_simulations"
    if selection == "Évolution":
        return "evolution"
    return "portfolio"


def open_analysis_view() -> None:
    clear_ephemeral_state_if_view_changes("analysis")
    st.session_state["cm_view"] = "analysis"
    st.query_params.clear()


def open_review_dates_view() -> None:
    clear_ephemeral_state_if_view_changes("review_dates")
    st.session_state["cm_view"] = "review_dates"
    st.query_params.clear()


def open_review_simulations_view() -> None:
    clear_ephemeral_state_if_view_changes("review_simulations")
    st.session_state["cm_view"] = "review_simulations"
    st.query_params.clear()


def open_evolution_view() -> None:
    clear_ephemeral_state_if_view_changes("evolution")
    st.session_state["cm_view"] = "evolution"
    st.query_params.clear()


def open_portfolio_view() -> None:
    clear_ephemeral_state_if_view_changes("portfolio")
    st.session_state["cm_view"] = "portfolio"
    st.query_params.clear()


def analysis_dimension_mapping(df: pd.DataFrame) -> dict[str, str]:
    candidates = {
        "Société": SOC_COL,
        "Segment": "Segment",
        "Pays": "Pays de résidence",
        "Produit": "Produit(service) principal",
        "Canal": "Canal d’opérations principal 12 mois",
        "Vigilance": "Vigilance",
        "Risque": "Risque",
        "Statut EDD": "Statut EDD",
        "Analyste": "Analyste",
        "Valideur": "Valideur",
        "Nationalité": "Nationalité",
        "Catégorie juridique": "Catégorie Juridique",
        "Cash intensité": "Cash intensité Statut",
        "Cross-border": "Cross border",
    }
    return {label: column for label, column in candidates.items() if column in df.columns}



def analysis_measure_mapping(df: pd.DataFrame) -> dict[str, str]:
    return {
        "Clients": "clients",
        "Part du portefeuille": "share",
        "Justificatifs incomplets": "missing_docs",
        "Sans prochaine revue": "without_next_review",
        "Revue trop ancienne": "stale_review",
        "Cross-border élevé": "cross_border_high",
        "Cash intensité élevée": "cash_intensity_high",
    }


def compute_measure_series(df: pd.DataFrame, measure_key: str) -> pd.Series:
    if df.empty:
        return pd.Series(dtype="float64")
    if measure_key == "clients":
        return pd.Series(1, index=df.index, dtype="int64")
    if measure_key == "critical_vigilance":
        return df.get("Vigilance", pd.Series(index=df.index, dtype="string")).isin(CRITICAL_VIGILANCE).astype(int)
    if measure_key == "confirmed_risk":
        return df.get("Risque", pd.Series(index=df.index, dtype="string")).eq("Risque avéré").astype(int)
    if measure_key == "edd_open":
        edd = df.get("Statut EDD", pd.Series(index=df.index, dtype="string")).astype("string").fillna("")
        return edd.str.lower().str.contains("ouvrir|ouverte|ouvert|cours", regex=True).astype(int)
    if measure_key == "missing_docs":
        return df.get("Flag justificatif complet", pd.Series(index=df.index, dtype="string")).ne("Oui").astype(int)
    if measure_key == "without_next_review":
        return df.get("Date prochaine revue", pd.Series(index=df.index, dtype="datetime64[ns]")).isna().astype(int)
    if measure_key == "cross_border":
        return df.get("Cross border", pd.Series(index=df.index, dtype="float64")).ge(0.25).fillna(False).astype(int)
    if measure_key == "history_cases":
        return df.get("Nb historique", pd.Series(index=df.index, dtype="float64")).fillna(0).gt(0).astype(int)
    return pd.Series(1, index=df.index, dtype="int64")


def build_analysis_main_table(
    df: pd.DataFrame,
    line_col: str,
    line_label: str,
    measure_key: str,
    measure_label: str,
    sort_desc: bool = True,
) -> tuple[pd.DataFrame, str]:
    if df.empty:
        return pd.DataFrame(columns=[line_label, "Clients", "% portefeuille"]), ""

    work = df.copy()
    work[line_col] = work.get(line_col).fillna("Non renseigné").astype(str).replace({"": "Non renseigné"})
    work["cm_client_key"] = work[SOC_COL].astype(str) + "|" + work["SIREN"].astype(str)
    work["cm_measure"] = compute_measure_series(work, measure_key).astype(float)
    work["cm_edd_open"] = work.get("Statut EDD", pd.Series(index=work.index, dtype="string")).astype("string").fillna("").str.lower().str.contains("ouvrir|ouverte|ouvert|cours", regex=True).astype(int)
    work["cm_without_next_review"] = work.get("Date prochaine revue", pd.Series(index=work.index, dtype="datetime64[ns]")).isna().astype(int)
    work["cm_missing_docs"] = work.get("Flag justificatif complet", pd.Series(index=work.index, dtype="string")).astype("string").fillna("").ne("Oui").astype(int)
    work["cm_gov_gap"] = (
        work.get("Alerte justificatif incomplet", pd.Series(0, index=work.index)).fillna(0).astype(int)
        + work.get("Alerte revue trop ancienne", pd.Series(0, index=work.index)).fillna(0).astype(int)
        + work.get("Alerte sans prochaine revue", pd.Series(0, index=work.index)).fillna(0).astype(int)
    )

    total_clients = max(int(work["cm_client_key"].nunique()), 1)
    total_measure = float(work["cm_measure"].sum())

    grouped = (
        work.groupby(line_col, dropna=False)
        .agg(
            Clients=("cm_client_key", "nunique"),
            Mesure=("cm_measure", "sum"),
            Vigilance_renforcee=("Vigilance", lambda s: s.isin(CRITICAL_VIGILANCE).sum()),
            Risques_averes=("Risque", lambda s: s.eq("Risque avéré").sum()),
            EDD_ouvertes=("cm_edd_open", "sum"),
            Sans_prochaine_revue=("cm_without_next_review", "sum"),
            Justificatifs_incomplets=("cm_missing_docs", "sum"),
            Ecarts_gouvernance=("cm_gov_gap", "sum"),
        )
        .reset_index()
        .rename(columns={line_col: line_label})
    )
    grouped["% portefeuille"] = grouped["Clients"].div(total_clients).fillna(0)
    grouped["% indicateur"] = grouped["Mesure"].div(total_measure).fillna(0) if total_measure else 0.0

    grouped = grouped.rename(columns={
        "Vigilance_renforcee": "Vigilance renforcée",
        "Risques_averes": "Risques avérés",
        "EDD_ouvertes": "EDD ouvertes",
        "Sans_prochaine_revue": "Sans prochaine revue",
        "Justificatifs_incomplets": "Justificatifs incomplets",
        "Ecarts_gouvernance": "Alertes de gouvernance (calculé)",
    })

    if measure_key in {"clients", "share"}:
        result = grouped[[
            line_label,
            "Clients",
            "% portefeuille",
            "Vigilance renforcée",
            "Risques avérés",
            "EDD ouvertes",
            "Sans prochaine revue",
            "Justificatifs incomplets",
            "Alertes de gouvernance (calculé)",
        ]].copy()
        sort_col = "Clients" if sort_desc else line_label
        ascending = False if sort_desc else True
        result = result.sort_values(sort_col, ascending=ascending, kind="stable")
        return result.reset_index(drop=True), f"Lecture du portefeuille par {line_label.lower()} sur le périmètre filtré."

    safe_measure_label = measure_label if measure_label not in grouped.columns else f"{measure_label} (indicateur)"
    grouped = grouped.rename(columns={"Mesure": safe_measure_label})
    result = grouped[[
        line_label,
        "Clients",
        "% portefeuille",
        safe_measure_label,
        "% indicateur",
        "Vigilance renforcée",
        "Risques avérés",
        "EDD ouvertes",
        "Sans prochaine revue",
        "Justificatifs incomplets",
        "Alertes de gouvernance (calculé)",
    ]].copy()
    sort_col = safe_measure_label if sort_desc else line_label
    ascending = False if sort_desc else True
    result = result.sort_values(sort_col, ascending=ascending, kind="stable")
    return result.reset_index(drop=True), f"Lecture du portefeuille par {line_label.lower()} avec l’indicateur « {measure_label} »."


def build_analysis_trend_table(df: pd.DataFrame) -> pd.DataFrame:
    def monthly_count(series: pd.Series, label: str) -> pd.Series:
        if series is None or series.empty:
            return pd.Series(dtype="int64", name=label)
        clean = pd.to_datetime(series, errors="coerce").dropna()
        if clean.empty:
            return pd.Series(dtype="int64", name=label)
        month = clean.dt.to_period("M").dt.to_timestamp()
        return month.value_counts().sort_index().rename(label)

    frames = [
        monthly_count(df.get("Vigilance Date de mise à jour"), "Mises à jour vigilance"),
        monthly_count(df.get("Date dernière revue"), "Dernières revues"),
        monthly_count(df.get("Date prochaine revue"), "Prochaines revues"),
    ]
    combined = pd.concat(frames, axis=1).fillna(0).sort_index()
    if combined.empty:
        return pd.DataFrame(columns=["Mois", "Mises à jour vigilance", "Dernières revues", "Prochaines revues", "% clients revus"])
    combined = combined.tail(6)
    combined["% clients revus"] = combined["Dernières revues"].div(max(len(df), 1))
    combined = combined.reset_index().rename(columns={"index": "Mois"})
    combined["Mois"] = pd.to_datetime(combined["Mois"]).dt.strftime("%Y-%m")
    return combined


def build_analysis_group_table(
    df: pd.DataFrame,
    group_col: str,
    group_label: str,
    measure_key: str,
    measure_label: str,
    *,
    sort_desc: bool = True,
    top_n: int = 12,
) -> tuple[pd.DataFrame, str]:
    if df.empty:
        return pd.DataFrame(columns=[group_label, "Clients", "% portf."]), ""
    work = df.copy()
    work[group_col] = work.get(group_col).fillna("Non renseigné").astype(str).replace({"": "Non renseigné"})
    work["cm_client_key"] = work[SOC_COL].astype(str) + "|" + work["SIREN"].astype(str)
    work["cm_measure"] = compute_measure_series(work, measure_key).astype(float)

    total_clients = max(int(work["cm_client_key"].nunique()), 1)
    total_measure = float(work["cm_measure"].sum())

    grouped = (
        work.groupby(group_col, dropna=False)
        .agg(
            Clients=("cm_client_key", "nunique"),
            Mesure=("cm_measure", "sum"),
            Vigilance=("Vigilance", lambda s: s.isin(CRITICAL_VIGILANCE).sum()),
            Risque=("Risque", lambda s: s.eq("Risque avéré").sum()),
        )
        .reset_index()
        .rename(columns={group_col: group_label, "Vigilance": "Vigilances critiques", "Risque": "Risques avérés"})
    )
    grouped["% portf."] = grouped["Clients"].div(total_clients).fillna(0)

    if measure_key in {"share", "clients"}:
        grouped = grouped[[group_label, "Clients", "% portf.", "Vigilances critiques", "Risques avérés"]]
        sort_col = "Clients" if sort_desc else group_label
        ascending = False if sort_desc else True
        grouped = grouped.sort_values(sort_col, ascending=ascending, kind="stable")
        return grouped.head(top_n).reset_index(drop=True), f"Répartition simple par {group_label.lower()} sur le périmètre filtré."

    safe_measure_label = measure_label if measure_label not in grouped.columns else f"{measure_label} (mesure)"
    grouped[safe_measure_label] = grouped["Mesure"]
    grouped["% mesure"] = grouped["Mesure"].div(total_measure).fillna(0) if total_measure else 0.0
    grouped = grouped[[group_label, "Clients", "% portf.", safe_measure_label, "% mesure", "Vigilances critiques", "Risques avérés"]]
    sort_col = safe_measure_label if sort_desc else group_label
    ascending = False if sort_desc else True
    grouped = grouped.sort_values(sort_col, ascending=ascending, kind="stable")
    return grouped.head(top_n).reset_index(drop=True), f"Répartition simple par {group_label.lower()} ; la mesure choisie est affichée séparément."


def build_analysis_cross_table(
    df: pd.DataFrame,
    row_col: str,
    row_label: str,
    col_col: str,
    col_label: str,
    measure_key: str,
    measure_label: str,
    *,
    sort_desc: bool = True,
    top_n: int = 14,
    focus_row_value: str | None = None,
    focus_col_value: str | None = None,
) -> tuple[pd.DataFrame, str]:
    if df.empty:
        return pd.DataFrame(columns=[row_label, col_label, "Clients"]), ""
    work = df.copy()
    work[row_col] = work.get(row_col).fillna("Non renseigné").astype(str).replace({"": "Non renseigné"})
    work[col_col] = work.get(col_col).fillna("Non renseigné").astype(str).replace({"": "Non renseigné"})
    work["cm_client_key"] = work[SOC_COL].astype(str) + "|" + work["SIREN"].astype(str)
    work["cm_measure"] = compute_measure_series(work, measure_key).astype(float)
    total_clients = max(int(work["cm_client_key"].nunique()), 1)
    total_measure = float(work["cm_measure"].sum())

    grouped = (
        work.groupby([row_col, col_col], dropna=False)
        .agg(
            Clients=("cm_client_key", "nunique"),
            Mesure=("cm_measure", "sum"),
            Vigilance=("Vigilance", lambda s: s.isin(CRITICAL_VIGILANCE).sum()),
            Risque=("Risque", lambda s: s.eq("Risque avéré").sum()),
        )
        .reset_index()
        .rename(columns={row_col: row_label, col_col: col_label, "Vigilance": "Vigilances critiques", "Risque": "Risques avérés"})
    )
    grouped["% portf."] = grouped["Clients"].div(total_clients).fillna(0)
    focus_active = focus_row_value not in {None, "", "Tous"} and focus_col_value not in {None, "", "Tous"}
    focus_mask = None
    if focus_active:
        focus_mask = (
            grouped[row_label].astype(str).eq(str(focus_row_value))
            & grouped[col_label].astype(str).eq(str(focus_col_value))
        )

    if measure_key in {"share", "clients"}:
        grouped = grouped[[row_label, col_label, "Clients", "% portf.", "Vigilances critiques", "Risques avérés"]]
        sort_col = "Clients" if sort_desc else row_label
        ascending = False if sort_desc else True
        grouped = grouped.sort_values(sort_col, ascending=ascending, kind="stable")
        if focus_active:
            focused = grouped.loc[focus_mask].reset_index(drop=True)
            caption = f"Croisement sélectionné : {row_label} = {focus_row_value} | {col_label} = {focus_col_value}."
            return focused, caption
        return grouped.head(top_n).reset_index(drop=True), f"Croisements majeurs entre {row_label.lower()} et {col_label.lower()}."

    safe_measure_label = measure_label if measure_label not in grouped.columns else f"{measure_label} (mesure)"
    grouped[safe_measure_label] = grouped["Mesure"]
    grouped["% mesure"] = grouped["Mesure"].div(total_measure).fillna(0) if total_measure else 0.0
    grouped = grouped[[row_label, col_label, "Clients", "% portf.", safe_measure_label, "% mesure", "Vigilances critiques", "Risques avérés"]]
    sort_col = safe_measure_label if sort_desc else row_label
    ascending = False if sort_desc else True
    grouped = grouped.sort_values(sort_col, ascending=ascending, kind="stable")
    if focus_active:
        focused = grouped.loc[focus_mask].reset_index(drop=True)
        caption = f"Croisement sélectionné : {row_label} = {focus_row_value} | {col_label} = {focus_col_value}."
        return focused, caption
    return grouped.head(top_n).reset_index(drop=True), f"Croisements majeurs entre {row_label.lower()} et {col_label.lower()} avec la mesure sélectionnée."


def render_analysis_panel_header(title: str, caption: str | None = None) -> None:
    st.markdown(f"<div class='cm-table-panel-title'>{escape(title)}</div>", unsafe_allow_html=True)
    if caption:
        st.markdown(f"<div class='cm-table-panel-caption'>{escape(caption)}</div>", unsafe_allow_html=True)



def render_selectable_analysis_table(
    df: pd.DataFrame,
    *,
    key_prefix: str,
    height: int = 420,
) -> tuple[str, list[dict[str, object]] | None]:
    if df is None or df.empty:
        st.info("Aucune donnée à afficher.")
        return "empty", None

    raw_df = df.copy().reset_index(drop=True)
    display_df = format_table_display_dataframe(raw_df)

    hint_left, hint_right, hint_clear = st.columns([6.0, 2.3, 1.5])
    with hint_left:
        st.markdown(
            "<div class='cm-analysis-hint-text'>Cliquez directement sur une ou plusieurs lignes du tableau pour définir le focus analytique et mettre à jour les clients sous-jacents.</div>",
            unsafe_allow_html=True,
        )
    with hint_right:
        st.markdown(
            "<div class='cm-analysis-hint-action'><a class='cm-analysis-jump-btn' href='#clients-sous-jacents'>Voir les clients sous-jacents</a></div>",
            unsafe_allow_html=True,
        )
    reset_counter_key = f"analysis_table_reset_counter_{key_prefix}"
    with hint_clear:
        st.markdown("<div style='height:0.15rem'></div>", unsafe_allow_html=True)
        if st.button("Effacer le focus", key=f"analysis_clear_{key_prefix}", type="secondary"):
            st.session_state[reset_counter_key] = int(st.session_state.get(reset_counter_key, 0)) + 1
            return "cleared", None

    column_config: dict[str, object] = {}
    for col in display_df.columns:
        if col in {"Vigilance", "Risque"}:
            column_config[col] = st.column_config.TextColumn(col, width="medium")
        elif col in {"EDD", "Segment", "Produit", "Analyste", "Valideur"}:
            column_config[col] = st.column_config.TextColumn(col, width="medium")
        elif col in {"Pays", "Canal"}:
            column_config[col] = st.column_config.TextColumn(col, width="small")
        else:
            column_config[col] = st.column_config.TextColumn(col, width="medium")

    table_version = int(st.session_state.get(reset_counter_key, 0))
    event = st.dataframe(
        style_interactive_table(display_df, raw_df),
        width="stretch",
        height=height,
        hide_index=True,
        column_order=list(display_df.columns),
        column_config=column_config,
        on_select="rerun",
        selection_mode="multi-row",
        row_height=40,
        key=f"cm_analysis_select_{key_prefix}_{table_version}",
    )

    selected_rows: list[int] = []
    if event is not None:
        try:
            selected_rows = [int(i) for i in event.selection.get("rows", [])]
        except Exception:
            selected_rows = []

    if selected_rows:
        valid_rows = [i for i in selected_rows if 0 <= i < len(raw_df)]
        if valid_rows:
            selected_records = raw_df.iloc[valid_rows].to_dict(orient="records")
            return "selected", selected_records

    if event is not None and "analysis_focus_selection" in st.session_state:
        return "cleared", None
    return "unchanged", None



def render_analysis_simple_table(df: pd.DataFrame) -> None:
    if df is None or df.empty:
        st.info("Aucune donnée à afficher.")
        return
    display_df = format_table_for_display(df)
    render_small_table(display_df)

def apply_analysis_table_controls(
    df: pd.DataFrame,
    *,
    line_label: str,
    default_sort_label: str,
) -> tuple[pd.DataFrame, dict[str, object]]:
    if df is None or df.empty:
        return df, {"sort_by": default_sort_label, "ascending": False, "search": "", "selected_labels": []}

    work = df.copy().reset_index(drop=True)
    control_cols = st.columns([1.4, 1.8, 1.1, 1.0, 0.9])
    with control_cols[0]:
        search_value = st.text_input(
            "Recherche",
            value=st.session_state.get("analysis_table_search", ""),
            key="analysis_table_search",
            placeholder=f"Filtrer {line_label.lower()}…",
        )
    with control_cols[1]:
        available_labels = non_empty_sorted(work[line_label].astype(str).unique())
        selected_labels = st.multiselect(
            f"{line_label}",
            options=available_labels,
            default=st.session_state.get("analysis_table_values", []),
            key="analysis_table_values",
            placeholder="Toutes les valeurs",
        )
    sort_options = [c for c in work.columns if c != line_label]
    if default_sort_label not in sort_options:
        default_sort_label = sort_options[0] if sort_options else line_label
    if st.session_state.get("analysis_table_sort_by") not in sort_options:
        st.session_state["analysis_table_sort_by"] = default_sort_label
    with control_cols[2]:
        sort_by = st.selectbox(
            "Trier par",
            options=sort_options,
            index=sort_options.index(st.session_state.get("analysis_table_sort_by", default_sort_label)) if sort_options else 0,
            key="analysis_table_sort_by",
        ) if sort_options else default_sort_label
    order_options = ["Décroissant", "Croissant"]
    if st.session_state.get("analysis_table_sort_order") not in order_options:
        st.session_state["analysis_table_sort_order"] = "Décroissant"
    with control_cols[3]:
        sort_order = st.selectbox(
            "Ordre",
            options=order_options,
            index=order_options.index(st.session_state.get("analysis_table_sort_order", "Décroissant")),
            key="analysis_table_sort_order",
        )
    with control_cols[4]:
        top_n = st.number_input(
            "Top N",
            min_value=0,
            max_value=max(len(work), 1),
            value=min(int(st.session_state.get("analysis_table_top_n", min(len(work), 12))), max(len(work), 1)),
            step=1,
            key="analysis_table_top_n",
            help="0 = toutes les lignes",
        )

    if search_value:
        mask = work[line_label].astype(str).str.contains(str(search_value), case=False, na=False)
        work = work[mask]
    if selected_labels:
        work = work[work[line_label].astype(str).isin([str(v) for v in selected_labels])]

    ascending = sort_order == "Croissant"
    if sort_by in work.columns:
        work = work.sort_values(sort_by, ascending=ascending, kind="stable")
    if int(top_n) > 0:
        work = work.head(int(top_n))
    work = work.reset_index(drop=True)
    return work, {
        "sort_by": sort_by,
        "ascending": ascending,
        "search": search_value,
        "selected_labels": selected_labels,
        "top_n": int(top_n),
    }


def normalize_indicators_current(indicators_df: pd.DataFrame) -> pd.DataFrame:
    if indicators_df is None or indicators_df.empty:
        return pd.DataFrame(columns=[SOC_COL, "SIREN", "Dénomination", "Indicateur", "Statut", "Valeur", "Date de mise à jour", "Commentaire"])

    groups = indicator_group_map(list(indicators_df.columns))
    rows: list[dict[str, object]] = []
    for _, row in indicators_df.iterrows():
        base_info = {
            SOC_COL: row.get(SOC_COL),
            "SIREN": row.get("SIREN"),
            "Dénomination": row.get("Dénomination"),
        }
        for indicator_name, mapping in groups.items():
            if indicator_name == "Vigilance":
                continue
            statut = row.get(mapping.get("Statut", ""), None)
            valeur = row.get(mapping.get("Valeur", ""), None)
            commentaire = row.get(mapping.get("Commentaire", ""), None)
            date_maj = row.get(mapping.get("Date de mise à jour", ""), None)
            if pd.isna(statut) and pd.isna(valeur) and pd.isna(commentaire) and pd.isna(date_maj):
                continue
            rows.append({
                **base_info,
                "Indicateur": indicator_name,
                "Statut": clean_text_column(pd.Series([statut])).iloc[0],
                "Valeur": clean_text_column(pd.Series([valeur])).iloc[0],
                "Date de mise à jour": pd.to_datetime(pd.Series([date_maj]), errors="coerce").iloc[0],
                "Commentaire": clean_text_column(pd.Series([commentaire])).iloc[0],
            })
    return pd.DataFrame(rows)



def analysis_indicator_base_columns() -> list[str]:
    return [
        SOC_COL,
        "SIREN",
        "Dénomination",
        "Indicateur",
        "Statut",
        "Valeur",
        "Date de mise à jour",
        "Commentaire",
        "Vigilance",
        "Risque",
        "Statut EDD",
        "Segment",
        "Pays de résidence",
        "Produit(service) principal",
        "Canal d’opérations principal 12 mois",
        "Analyste",
        "Valideur",
        "Date dernière revue",
        "Date prochaine revue",
        "Vigilance Date de mise à jour",
        "Famille indicateur",
        "Fraîcheur indicateur",
        "cm_client_key",
    ]



def build_analysis_indicator_scope_dataset(filtered_portfolio: pd.DataFrame, normalized_indicators_df: pd.DataFrame) -> pd.DataFrame:
    base_columns = analysis_indicator_base_columns()
    if filtered_portfolio is None or filtered_portfolio.empty:
        return pd.DataFrame(columns=base_columns)
    if normalized_indicators_df is None or normalized_indicators_df.empty:
        return pd.DataFrame(columns=base_columns)

    portfolio_join_columns = [
        SOC_COL,
        "SIREN",
        "Vigilance",
        "Risque",
        "Statut EDD",
        "Segment",
        "Pays de résidence",
        "Produit(service) principal",
        "Canal d’opérations principal 12 mois",
        "Analyste",
        "Valideur",
        "Date dernière revue",
        "Date prochaine revue",
        "Vigilance Date de mise à jour",
    ]
    portfolio_join_columns = [col for col in portfolio_join_columns if col in filtered_portfolio.columns]
    client_scope = build_unique_client_snapshot(filtered_portfolio, portfolio_join_columns)
    merged = normalized_indicators_df.merge(
        client_scope.drop(columns=["cm_client_key"], errors="ignore"),
        how="inner",
        on=[col for col in [SOC_COL, "SIREN"] if col in client_scope.columns],
    )
    if merged.empty:
        return pd.DataFrame(columns=base_columns)

    merged["Statut"] = merged["Statut"].apply(lambda value: canonical_risk_label(value) or ("" if value is None or pd.isna(value) else str(value).strip()))
    merged["Date de mise à jour"] = pd.to_datetime(merged.get("Date de mise à jour"), errors="coerce")
    merged["Famille indicateur"] = merged["Indicateur"].apply(classify_analysis_indicator_family)
    merged["Fraîcheur indicateur"] = merged["Date de mise à jour"].apply(analysis_freshness_bucket)
    merged["cm_client_key"] = merged[SOC_COL].astype(str).str.strip() + "|" + merged["SIREN"].astype(str).str.strip()

    for column_name in base_columns:
        if column_name not in merged.columns:
            merged[column_name] = pd.NA
    return merged[base_columns].copy()



def build_analysis_indicator_dataset(filtered_portfolio: pd.DataFrame, indicators_df: pd.DataFrame) -> pd.DataFrame:
    normalized = normalize_indicators_current(indicators_df)
    return build_analysis_indicator_scope_dataset(filtered_portfolio, normalized)


@st.cache_data(show_spinner=False)
def get_analysis_normalized_indicators_cached(
    dataset_signature: str,
    analysis_cache_version: str,
    societies_key: tuple[str, ...],
) -> pd.DataFrame:
    _base, indicators, _history, _portfolio = get_app_datasets_cached(dataset_signature)
    scoped_indicators = restrict_to_societies(indicators, list(societies_key))
    return normalize_indicators_current(scoped_indicators)


@st.cache_data(show_spinner=False)
def get_analysis_indicator_scope_cached(
    dataset_signature: str,
    analysis_cache_version: str,
    societies_key: tuple[str, ...],
) -> pd.DataFrame:
    _base, _indicators, _history, portfolio = get_app_datasets_cached(dataset_signature)
    scoped_portfolio = restrict_to_societies(portfolio, list(societies_key))
    normalized = get_analysis_normalized_indicators_cached(dataset_signature, analysis_cache_version, societies_key)
    return build_analysis_indicator_scope_dataset(scoped_portfolio, normalized)



def restrict_analysis_indicator_scope_to_portfolio(
    analysis_scope_df: pd.DataFrame,
    filtered_portfolio: pd.DataFrame,
) -> pd.DataFrame:
    base_columns = analysis_indicator_base_columns()
    if analysis_scope_df is None or analysis_scope_df.empty:
        return pd.DataFrame(columns=base_columns)
    if filtered_portfolio is None or filtered_portfolio.empty:
        return pd.DataFrame(columns=base_columns)

    if "cm_client_key" in filtered_portfolio.columns:
        raw_keys = filtered_portfolio["cm_client_key"]
    elif SOC_COL in filtered_portfolio.columns and "SIREN" in filtered_portfolio.columns:
        raw_keys = filtered_portfolio[SOC_COL].astype(str).str.strip() + "|" + filtered_portfolio["SIREN"].astype(str).str.strip()
    else:
        raw_keys = pd.Series(dtype="object")

    key_set = {str(value).strip() for value in raw_keys if pd.notna(value) and str(value).strip()}
    if not key_set:
        return pd.DataFrame(columns=base_columns)

    work = analysis_scope_df[analysis_scope_df["cm_client_key"].astype(str).isin(key_set)].copy()
    if work.empty:
        return pd.DataFrame(columns=base_columns)
    for column_name in base_columns:
        if column_name not in work.columns:
            work[column_name] = pd.NA
    return work[base_columns].reset_index(drop=True)



def normalize_filter_cache_key(filters: dict[str, object], ordered_keys: list[str]) -> tuple[tuple[str, str], ...]:
    return tuple((key, str(filters.get(key, "Tous") or "Tous")) for key in ordered_keys)


@st.cache_data(show_spinner=False)
def get_analysis_base_for_portfolio_filters_cached(
    dataset_signature: str,
    analysis_cache_version: str,
    societies_key: tuple[str, ...],
    portfolio_filters_key: tuple[tuple[str, str], ...],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    _base, _indicators, _history, portfolio = get_app_datasets_cached(dataset_signature)
    scoped_portfolio = restrict_to_societies(portfolio, list(societies_key))
    filtered_portfolio = apply_filters(scoped_portfolio, dict(portfolio_filters_key))
    analysis_scope = get_analysis_indicator_scope_cached(dataset_signature, analysis_cache_version, societies_key)
    analysis_base = restrict_analysis_indicator_scope_to_portfolio(analysis_scope, filtered_portfolio)
    return filtered_portfolio, analysis_base


@st.cache_data(show_spinner=False)
def get_analysis_filtered_scope_cached(
    dataset_signature: str,
    analysis_cache_version: str,
    societies_key: tuple[str, ...],
    portfolio_filters_key: tuple[tuple[str, str], ...],
    indicator_filters_key: tuple[tuple[str, str], ...],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    filtered_portfolio, analysis_base = get_analysis_base_for_portfolio_filters_cached(
        dataset_signature,
        analysis_cache_version,
        societies_key,
        portfolio_filters_key,
    )
    filtered_indicators = apply_analysis_indicator_filters(analysis_base, dict(indicator_filters_key))
    analysis_client_scope = build_analysis_client_scope(filtered_portfolio, filtered_indicators)
    return filtered_indicators, analysis_client_scope



def apply_analysis_indicator_filters(indicator_df: pd.DataFrame, filters: dict[str, object]) -> pd.DataFrame:
    if indicator_df is None or indicator_df.empty:
        return indicator_df

    work = indicator_df.copy()
    indicator_value = str(filters.get("Indicateur", "Tous") or "Tous")
    if indicator_value != "Tous":
        work = work[work["Indicateur"].astype(str) == indicator_value]

    status_value = str(filters.get("Statut", "Tous") or "Tous")
    if status_value != "Tous":
        canonical_status = canonical_risk_label(status_value) or status_value
        work = work[work["Statut"].astype(str) == canonical_status]

    family_value = str(filters.get("Famille", "Tous") or "Tous")
    if family_value != "Tous":
        work = work[work["Famille indicateur"].astype(str) == family_value]

    freshness_value = str(filters.get("Fraîcheur", "Tous") or "Tous")
    if freshness_value != "Tous":
        work = work[work["Fraîcheur indicateur"].astype(str) == freshness_value]

    return work.reset_index(drop=True)


def build_analysis_client_scope(filtered_portfolio: pd.DataFrame, indicator_df: pd.DataFrame) -> pd.DataFrame:
    if filtered_portfolio is None or filtered_portfolio.empty or indicator_df is None or indicator_df.empty:
        return filtered_portfolio.iloc[0:0].copy() if isinstance(filtered_portfolio, pd.DataFrame) else pd.DataFrame()
    keys = indicator_df[[SOC_COL, "SIREN"]].drop_duplicates()
    return filtered_portfolio.merge(keys, how="inner", on=[SOC_COL, "SIREN"]).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def build_analysis_status_distribution(indicator_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total_cases = int(len(indicator_df)) if indicator_df is not None else 0
    series = indicator_df.get("Statut", pd.Series(dtype="object")) if indicator_df is not None else pd.Series(dtype="object")
    for status in ANALYSIS_STATUS_ORDER:
        count_value = int(series.astype(str).eq(status).sum()) if not series.empty else 0
        rows.append({"Statut": analysis_status_ui_label(status), "Cas": count_value, "%": (count_value / total_cases if total_cases else 0.0)})
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def build_analysis_family_distribution(indicator_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total_cases = int(len(indicator_df)) if indicator_df is not None else 0
    for family in ANALYSIS_FAMILY_ORDER:
        if indicator_df is None or indicator_df.empty:
            client_count = 0
            case_count = 0
        else:
            scoped = indicator_df[indicator_df["Famille indicateur"].astype(str) == family]
            client_count = int(scoped.get("cm_client_key", pd.Series(dtype="object")).nunique())
            case_count = int(len(scoped))
        rows.append({"Famille": family, "Clients": client_count, "Cas": case_count, "% cas": (case_count / total_cases if total_cases else 0.0)})
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def build_analysis_freshness_distribution(indicator_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total_cases = int(len(indicator_df)) if indicator_df is not None else 0
    series = indicator_df.get("Fraîcheur indicateur", pd.Series(dtype="object")) if indicator_df is not None else pd.Series(dtype="object")
    for bucket in ANALYSIS_FRESHNESS_ORDER:
        count_value = int(series.astype(str).eq(bucket).sum()) if not series.empty else 0
        rows.append({"Fraîcheur": bucket, "Cas": count_value, "%": (count_value / total_cases if total_cases else 0.0)})
    return pd.DataFrame(rows)


def render_analysis_alert_kpis(filtered_portfolio: pd.DataFrame, analysis_client_scope: pd.DataFrame, indicator_df: pd.DataFrame) -> None:
    total_clients_filtered = int(build_unique_client_snapshot(filtered_portfolio).shape[0]) if isinstance(filtered_portfolio, pd.DataFrame) else 0
    concerned_clients = int(build_unique_client_snapshot(analysis_client_scope).shape[0]) if isinstance(analysis_client_scope, pd.DataFrame) else 0
    total_cases = int(len(indicator_df)) if indicator_df is not None else 0
    distinct_indicators = int(indicator_df.get("Indicateur", pd.Series(dtype="object")).nunique()) if indicator_df is not None else 0
    part_of_scope = (concerned_clients / total_clients_filtered) if total_clients_filtered else 0.0

    line_one_cards = [
        ("Clients concernés", f"{concerned_clients:,}".replace(",", " "), "Au moins 1 indicateur d’alerte", " is-alert" if concerned_clients else ""),
        ("Cas indicateurs", f"{total_cases:,}".replace(",", " "), "Occurrences visibles", ""),
        ("Indicateurs distincts", f"{distinct_indicators:,}".replace(",", " "), "Indicateurs présents", ""),
        ("Part du portefeuille filtré", f"{part_of_scope:.1%}".replace(".", ","), "Clients concernés / portefeuille filtré", ""),
    ]

    line_two_cards = []
    status_series = indicator_df.get("Statut", pd.Series(dtype="object")) if indicator_df is not None else pd.Series(dtype="object")
    for status in ANALYSIS_STATUS_ORDER:
        count_value = int(status_series.astype(str).eq(status).sum()) if not status_series.empty else 0
        extra_class = " is-alert" if status in {"Risque avéré", "Risque potentiel", "Non calculable"} and count_value > 0 else ""
        line_two_cards.append((analysis_status_ui_label(status), f"{count_value:,}".replace(",", " "), "Cas d’indicateurs", extra_class))

    st.markdown('<h3 class="cm-section-title">Bandeau de synthèse</h3>', unsafe_allow_html=True)
    for cards in [line_one_cards, line_two_cards]:
        st.markdown(
            "<div class='cm-kpi-band'>"
            + "".join(
                f"<div class='cm-kpi-card{extra_class}'><div class='cm-kpi-label'>{escape(label)}</div><div class='cm-kpi-value'>{escape(value)}</div><div class='cm-kpi-sub'>{escape(sub)}</div></div>"
                for label, value, sub, extra_class in cards
            )
            + "</div>",
            unsafe_allow_html=True,
        )

    if indicator_df is not None and not indicator_df.empty:
        last_update = pd.to_datetime(indicator_df.get("Date de mise à jour"), errors="coerce").max()
        if pd.notna(last_update):
            st.markdown(
                f"<div class='cm-kpi-note'>Dernière mise à jour indicateur visible : <strong>{last_update.strftime('%d/%m/%Y')}</strong>. Ces calculs sont propres à l’écran Analyse et n’impactent pas l’écran Portefeuille.</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='cm-kpi-note'>Ces calculs sont propres à l’écran Analyse et n’impactent pas l’écran Portefeuille.</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            "<div class='cm-kpi-note'>Ces calculs sont propres à l’écran Analyse et n’impactent pas l’écran Portefeuille.</div>",
            unsafe_allow_html=True,
        )


def render_analysis_repartition(
    indicator_df: pd.DataFrame,
    *,
    status_distribution: pd.DataFrame | None = None,
    family_distribution: pd.DataFrame | None = None,
    freshness_distribution: pd.DataFrame | None = None,
) -> None:
    render_analysis_panel_header(
        "Répartition",
        "Lecture des alertes par statut, par famille d’indicateurs et par fraîcheur de mise à jour. Les familles sont strictement cloisonnées : Segment / Client, Pays, Produits, Canal.",
    )
    if status_distribution is None:
        status_distribution = build_analysis_status_distribution(indicator_df)
    if family_distribution is None:
        family_distribution = build_analysis_family_distribution(indicator_df)
    if freshness_distribution is None:
        freshness_distribution = build_analysis_freshness_distribution(indicator_df)

    col_status, col_family, col_freshness = st.columns(3)
    with col_status:
        st.markdown("<div class='cm-table-panel-title' style='font-size:16px;'>Statuts des indicateurs</div>", unsafe_allow_html=True)
        render_small_table(format_table_for_display(status_distribution))
    with col_family:
        st.markdown("<div class='cm-table-panel-title' style='font-size:16px;'>Familles d’indicateurs</div>", unsafe_allow_html=True)
        render_small_table(format_table_for_display(family_distribution))
    with col_freshness:
        st.markdown("<div class='cm-table-panel-title' style='font-size:16px;'>Fraîcheur</div>", unsafe_allow_html=True)
        render_small_table(format_table_for_display(freshness_distribution))


def _format_analysis_top_cell(value: object, column_name: str) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)) or pd.isna(value):
        return ""
    if isinstance(value, (int, float, np.number)) and str(column_name).startswith("%"):
        return f"{float(value):.1%}".replace(".", ",")
    if isinstance(value, (int, np.integer)) or (isinstance(value, float) and float(value).is_integer()):
        return f"{int(value):,}".replace(",", " ")
    return escape(str(value))


def analysis_top_cell_style(column_name: str, value: object) -> str:
    if str(column_name) not in ANALYSIS_TOP_PERCENT_STYLE:
        return ""
    try:
        share_value = float(value)
    except Exception:
        return ""
    if not np.isfinite(share_value) or share_value <= 0:
        return ""
    style_meta = ANALYSIS_TOP_PERCENT_STYLE[str(column_name)]
    red, green, blue = _hex_to_rgb(style_meta["base"])
    intensity = min(max(share_value, 0.0) / 0.40, 1.0)
    start_alpha = 0.08 + 0.14 * intensity
    end_alpha = 0.18 + 0.36 * intensity
    border_alpha = 0.14 + 0.30 * intensity
    return (
        f"background: linear-gradient(90deg, rgba({red}, {green}, {blue}, {start_alpha:.3f}), rgba({red}, {green}, {blue}, {end_alpha:.3f}));"
        f" color:{style_meta['text']}; font-weight:700;"
        f" box-shadow: inset 0 0 0 1px rgba({red}, {green}, {blue}, {border_alpha:.3f});"
    )


def _build_analysis_top_table_html(df: pd.DataFrame) -> str:
    html = ["<div class='cm-mini-table-wrap' style='overflow-x: auto; overflow-y: hidden;'><table class='cm-mini-table'><thead><tr>"]
    for col in df.columns:
        html.append(f"<th>{escape(str(col))}</th>")
    html.append("</tr></thead><tbody>")

    for _, row in df.iterrows():
        html.append("<tr>")
        for col in df.columns:
            value = row[col]
            classes = []
            if pd.api.types.is_number(value) and not isinstance(value, bool):
                classes.append("cm-number")
            class_attr = f" class='{' '.join(classes)}'" if classes else ""
            style = analysis_top_cell_style(str(col), value)
            style_attr = f" style='{style}'" if style else ""
            rendered = _format_analysis_top_cell(value, str(col))
            html.append(f"<td{class_attr}{style_attr}>{rendered}</td>")
        html.append("</tr>")
    html.append("</tbody></table></div>")
    return "".join(html)


if hasattr(st, "dialog"):
    @st.dialog("Vue agrandie", width="large", icon=":material/open_in_full:")
    def show_analysis_top_dialog(title: str, df: pd.DataFrame) -> None:
        st.markdown(f'<div class="cm-subsection-title">{escape(title)}</div>', unsafe_allow_html=True)
        if df is None or df.empty:
            st.info("Aucune donnée à afficher.")
            return
        st.markdown(_build_analysis_top_table_html(df), unsafe_allow_html=True)
else:
    def show_analysis_top_dialog(title: str, df: pd.DataFrame) -> None:
        st.info("La vue agrandie nécessite une version plus récente de Streamlit prenant en charge st.dialog.")


def _build_analysis_top_preview_html(df: pd.DataFrame, sort_mode: str) -> str:
    if df is None or df.empty:
        return (
            "<div style='background:#FFFFFF;border:1px solid rgba(22,58,89,0.08);border-radius:18px;padding:14px 16px;box-shadow:0 12px 28px rgba(15,23,42,0.05);'>"
            "<div style='font-size:13px;color:#526273;'>Aucune donnée à afficher.</div>"
            "</div>"
        )

    top_rows = df.head(3).copy()
    rows_html: list[str] = []
    for rank, row in enumerate(top_rows.to_dict('records'), start=1):
        label = escape(str(row.get('Indicateurs', '')))
        metric_raw = row.get(sort_mode, '') if sort_mode in top_rows.columns else ''
        metric_display = _format_analysis_top_cell(metric_raw, sort_mode) if sort_mode in top_rows.columns else ''
        metric_style = analysis_top_cell_style(sort_mode, metric_raw) if sort_mode in top_rows.columns else ''
        metric_style = metric_style + " padding:4px 8px; border-radius:999px; white-space:nowrap; font-size:12px; font-weight:700;" if metric_display else metric_style
        metric_attr = f" style='{metric_style}'" if metric_display and metric_style else " style='white-space:nowrap;font-size:12px;font-weight:700;color:#526273;'"
        metric_html = f"<div{metric_attr}>{metric_display}</div>" if metric_display else ''
        border_style = "border-bottom:1px solid rgba(22,58,89,0.08);" if rank < len(top_rows) else ""
        rows_html.append(
            f"<div style='display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding:9px 0;{border_style}'>"
            f"<div style='display:flex;align-items:flex-start;gap:10px;min-width:0;'>"
            f"<div style='min-width:22px;font-family:Sora,sans-serif;font-weight:800;font-size:13px;color:#163A59;'>{rank}.</div>"
            f"<div style='font-family:Sora,sans-serif;font-weight:700;font-size:14px;line-height:1.35;color:#163A59;word-break:break-word;'>{label}</div>"
            f"</div>"
            f"{metric_html}"
            f"</div>"
        )

    return (
        "<div style='background:#FFFFFF;border:1px solid rgba(22,58,89,0.08);border-radius:18px;padding:14px 16px;box-shadow:0 12px 28px rgba(15,23,42,0.05);'>"
        f"<div style='font-size:12px;color:#526273;margin-bottom:2px;'>Top 3 selon le tri <strong style='color:#163A59;'>{escape(str(sort_mode))}</strong>.</div>"
        + ''.join(rows_html)
        + "</div>"
    )



def render_analysis_top_block(title: str, df: pd.DataFrame, *, dialog_key: str | None = None, sort_mode: str = "Nb") -> None:
    title_col, action_col = st.columns([6.4, 0.8])
    with title_col:
        st.markdown(f'<h3 class="cm-section-title" style="white-space: nowrap; margin-bottom: 0;">{escape(title)}</h3>', unsafe_allow_html=True)
    with action_col:
        st.markdown("<div style='height: 0.10rem;'></div>", unsafe_allow_html=True)
        if dialog_key and st.button(
            " ",
            key=f"analysis_expand_{dialog_key}",
            type="tertiary",
            icon=":material/open_in_full:",
            width="content",
            help="Ouvrir ce tableau dans une vue agrandie, sans modifier l'écran principal.",
        ):
            show_analysis_top_dialog(title, df)

    if df is None or df.empty:
        st.info("Aucune donnée à afficher.")
        return

    st.markdown(_build_analysis_top_preview_html(df, sort_mode), unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def build_analysis_indicator_top_table(
    indicator_df: pd.DataFrame,
    *,
    family_label: str,
    sort_mode: str = "Nb",
) -> pd.DataFrame:
    output_columns = ["Indicateurs", "Nb", "%"]
    for _, count_col, pct_col in ANALYSIS_TOP_STATUS_SPECS:
        output_columns.extend([count_col, pct_col])

    if indicator_df is None or indicator_df.empty:
        return pd.DataFrame(columns=output_columns)

    scoped = indicator_df[indicator_df["Famille indicateur"].astype(str) == family_label].copy()
    if scoped.empty:
        return pd.DataFrame(columns=output_columns)

    scoped["Indicateur"] = scoped["Indicateur"].astype(str).str.strip().replace({"": "Non renseigné"})
    grouped = scoped.groupby("Indicateur", dropna=False).size().reset_index(name="Nb")
    total_cases = int(len(scoped))
    grouped["%"] = grouped["Nb"].div(total_cases if total_cases else np.nan).fillna(0.0)

    for status, count_col, pct_col in ANALYSIS_TOP_STATUS_SPECS:
        status_counts = scoped.loc[scoped["Statut"].astype(str) == status].groupby("Indicateur", dropna=False).size()
        denominator = int(status_counts.sum())
        grouped[count_col] = grouped["Indicateur"].map(status_counts).fillna(0).astype(int)
        grouped[pct_col] = grouped["Indicateur"].map(status_counts).fillna(0).astype(float)
        grouped[pct_col] = grouped[pct_col].div(denominator if denominator else np.nan).fillna(0.0)

    grouped = grouped.rename(columns={"Indicateur": "Indicateurs"})

    sort_column = str(sort_mode or "Nb")
    if sort_column not in grouped.columns:
        sort_column = "Nb"
    grouped = grouped.sort_values([sort_column, "Nb", "Indicateurs"], ascending=[False, False, True], kind="stable")
    return grouped[output_columns].reset_index(drop=True)


def render_analysis_concentrations(
    indicator_df: pd.DataFrame,
    analysis_client_scope: pd.DataFrame | None = None,
    *,
    precomputed_tables: dict[str, pd.DataFrame] | None = None,
    sort_mode: str | None = None,
) -> None:
    render_analysis_panel_header(
        "Concentrations",
        "Chaque bloc affiche uniquement le top 3 en vue normale. Ouvrez la vue agrandie pour consulter le tableau détaillé complet et ses couleurs de lecture sur les pourcentages.",
    )
    current_sort_mode = st.session_state.get("analysis_top_sort_mode", sort_mode or "Nb")
    if current_sort_mode not in ANALYSIS_TOP_SORT_OPTIONS:
        current_sort_mode = sort_mode or "Nb"
    sort_mode = st.selectbox(
        "Trier les tableaux top par",
        options=ANALYSIS_TOP_SORT_OPTIONS,
        index=ANALYSIS_TOP_SORT_OPTIONS.index(current_sort_mode) if current_sort_mode in ANALYSIS_TOP_SORT_OPTIONS else 0,
        key="analysis_top_sort_mode",
    )

    row_one_left, row_one_right = st.columns(2)
    row_two_left, row_two_right = st.columns(2)
    containers = [row_one_left, row_one_right, row_two_left, row_two_right]
    for container, config in zip(containers, ANALYSIS_TOP_AXIS_CONFIG):
        title, family_label, dialog_key = config
        with container:
            if precomputed_tables is not None and family_label in precomputed_tables:
                table = precomputed_tables[family_label]
            else:
                table = build_analysis_indicator_top_table(
                    indicator_df,
                    family_label=family_label,
                    sort_mode=sort_mode,
                )
            render_analysis_top_block(title, table, dialog_key=dialog_key, sort_mode=sort_mode)


def build_analysis_screen_payload(
    dataset_signature: str,
    analysis_cache_version: str,
    societies_key: tuple[str, ...],
    portfolio_filters_key: tuple[tuple[str, str], ...],
    indicator_filters_key: tuple[tuple[str, str], ...],
    *,
    sort_mode: str = "Nb",
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> dict[str, object]:
    total_steps = 9

    def _step(step_number: int, label: str) -> None:
        if progress_callback is not None:
            progress_callback(step_number, total_steps, label)

    _step(1, "Chargement du portefeuille filtré")
    filtered_portfolio, analysis_base = get_analysis_base_for_portfolio_filters_cached(
        dataset_signature,
        analysis_cache_version,
        societies_key,
        portfolio_filters_key,
    )

    _step(2, "Chargement des cas indicateurs")
    filtered_indicators, analysis_client_scope = get_analysis_filtered_scope_cached(
        dataset_signature,
        analysis_cache_version,
        societies_key,
        portfolio_filters_key,
        indicator_filters_key,
    )

    _step(3, "Calcul de la répartition par statut")
    status_distribution = build_analysis_status_distribution(filtered_indicators)

    _step(4, "Calcul de la répartition par famille")
    family_distribution = build_analysis_family_distribution(filtered_indicators)

    _step(5, "Calcul de la répartition par fraîcheur")
    freshness_distribution = build_analysis_freshness_distribution(filtered_indicators)

    _step(6, "Préparation des tops Segment / Client et Pays")
    top_tables: dict[str, pd.DataFrame] = {}
    for family_label in ["Segment / Client", "Indicateurs Pays"]:
        top_tables[family_label] = build_analysis_indicator_top_table(
            filtered_indicators,
            family_label=family_label,
            sort_mode=sort_mode,
        )

    _step(7, "Préparation des tops Produits et Canaux")
    for family_label in ["Indicateurs Produits", "Indicateurs Canal"]:
        top_tables[family_label] = build_analysis_indicator_top_table(
            filtered_indicators,
            family_label=family_label,
            sort_mode=sort_mode,
        )

    _step(8, "Classement des indicateurs les plus contributifs")
    indicator_table = build_indicator_analysis_table(filtered_indicators)

    _step(9, "Finalisation de l’écran Analyse")
    return {
        "filtered_portfolio": filtered_portfolio,
        "analysis_base": analysis_base,
        "filtered_indicators": filtered_indicators,
        "analysis_client_scope": analysis_client_scope,
        "status_distribution": status_distribution,
        "family_distribution": family_distribution,
        "freshness_distribution": freshness_distribution,
        "top_tables": top_tables,
        "indicator_table": indicator_table,
        "sort_mode": sort_mode,
    }



@st.cache_data(show_spinner=False)
def build_indicator_analysis_table(indicator_scope: pd.DataFrame) -> pd.DataFrame:
    columns = ["Indicateur"] + ANALYSIS_STATUS_ORDER + ["Total cas"]
    if indicator_scope is None or indicator_scope.empty:
        return pd.DataFrame(columns=columns)

    work = indicator_scope.copy()
    crosstab = pd.crosstab(work["Indicateur"], work["Statut"])
    for status in ANALYSIS_STATUS_ORDER:
        if status not in crosstab.columns:
            crosstab[status] = 0
    crosstab["Total cas"] = crosstab[ANALYSIS_STATUS_ORDER].sum(axis=1)
    result = crosstab.reset_index().sort_values(["Total cas", "Indicateur"], ascending=[False, True], kind="stable")
    return result[columns].head(10).reset_index(drop=True)


def render_indicator_contribution_chart(indicator_table: pd.DataFrame) -> None:
    if indicator_table is None or indicator_table.empty:
        st.info("Aucun indicateur exploitable n’est disponible sur le périmètre filtré.")
        return

    df = indicator_table.copy().head(10).reset_index(drop=True)
    numeric_cols = ANALYSIS_STATUS_ORDER + ["Total cas"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    max_total = int(df["Total cas"].max()) if "Total cas" in df.columns and not df.empty else 0
    if max_total <= 0:
        max_total = 1

    chip_colors = {
        "Risque avéré": "#B42318",
        "Risque potentiel": "#175CD3",
        "Risque mitigé": "#027A48",
        "Risque levé": "#166534",
        "Non calculable": "#667085",
        "Aucun risque détecté": "#0F4C81",
    }

    rows: list[str] = []
    for rank, row in enumerate(df.to_dict("records"), start=1):
        total = int(row.get("Total cas", 0))
        width = max(6.0, round((total / max_total) * 100, 1))
        rank_bg = PRIMARY_COLOR if rank == 1 else (SECONDARY_COLOR if rank <= 3 else "#E9F1FA")
        rank_fg = "#FFFFFF" if rank <= 3 else PRIMARY_COLOR
        label = escape(str(row.get("Indicateur", "")))
        chips = []
        for status in ANALYSIS_STATUS_ORDER:
            chip_value = int(row.get(status, 0))
            chip_color = chip_colors.get(status, "#667085")
            chip_label = analysis_status_short_label(status)
            chips.append(
                f"<span style='display:inline-flex;align-items:center;gap:6px;padding:4px 8px;border-radius:999px;background:#F5F8FC;border:1px solid rgba(22,58,89,0.08);font-size:11px;color:#445469;'>"
                f"<span style='width:8px;height:8px;border-radius:999px;background:{chip_color};display:inline-block;'></span>"
                f"{escape(chip_label)} : <strong style='color:#163A59;font-weight:700;'>{chip_value}</strong>"
                f"</span>"
            )
        rows.append(
            f"<div style='display:flex;gap:12px;align-items:flex-start;padding:12px 0;border-bottom:1px solid rgba(22,58,89,0.08);'>"
            f"<div style='min-width:34px;width:34px;height:34px;border-radius:999px;background:{rank_bg};color:{rank_fg};display:flex;align-items:center;justify-content:center;font-family:Sora,sans-serif;font-weight:800;font-size:14px;'>{rank}</div>"
            f"<div style='flex:1;min-width:0;'>"
            f"<div style='display:flex;justify-content:space-between;align-items:flex-start;gap:16px;'>"
            f"<div style='font-family:Sora,sans-serif;font-weight:700;font-size:15px;line-height:1.35;color:#163A59;'>{label}</div>"
            f"<div style='white-space:nowrap;font-family:Sora,sans-serif;font-weight:800;font-size:16px;color:#163A59;'>{total} cas</div>"
            f"</div>"
            f"<div style='margin-top:8px;height:14px;border-radius:999px;background:#E8EFF7;overflow:hidden;'>"
            f"<div style='width:{width}%;height:100%;border-radius:999px;background:linear-gradient(90deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%);'></div>"
            f"</div>"
            f"<div style='display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;'>{''.join(chips)}</div>"
            f"</div>"
            f"</div>"
        )

    html = (
        "<div style='background:#FFFFFF;border:1px solid rgba(22,58,89,0.08);border-radius:20px;padding:18px 20px 10px 20px;box-shadow:0 12px 30px rgba(15,23,42,0.06);'>"
        "<div style='display:flex;justify-content:space-between;align-items:flex-end;gap:16px;margin-bottom:6px;'>"
        "<div>"
        "<div style='font-size:11px;letter-spacing:0.18em;text-transform:uppercase;font-weight:800;color:#5E8FC7;'>Top 10</div>"
        "<div style='font-family:Sora,sans-serif;font-weight:800;font-size:20px;color:#163A59;'>Indicateurs les plus contributifs</div>"
        "</div>"
        "<div style='font-size:12px;color:#526273;text-align:right;'>Classement établi sur le <strong style='color:#163A59;'>total de cas</strong>.</div>"
        "</div>"
        + ''.join(rows)
        + "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_analysis_trend_chart(trend_df: pd.DataFrame) -> None:
    if trend_df is None or trend_df.empty:
        st.info("Aucune date exploitable n'est disponible sur le périmètre filtré.")
        return

    chart_df = trend_df.copy()
    metric_cols = ["Mises à jour vigilance", "Dernières revues", "Prochaines revues"]
    for col in metric_cols:
        if col in chart_df.columns:
            chart_df[col] = pd.to_numeric(chart_df[col], errors="coerce").fillna(0).round(0).astype(int)

    month_order = chart_df["Mois"].astype(str).tolist()
    melted = chart_df.melt(
        id_vars=["Mois"],
        value_vars=metric_cols,
        var_name="Jalon",
        value_name="Cas",
    )
    melted["Mois"] = melted["Mois"].astype(str)
    melted["Cas"] = pd.to_numeric(melted["Cas"], errors="coerce").fillna(0).astype(int)

    color_scale = alt.Scale(
        domain=metric_cols,
        range=["#0F4C81", "#F28C28", "#2E8B57"],
    )

    base = alt.Chart(melted).encode(
        x=alt.X(
            "Mois:N",
            sort=month_order,
            title=None,
            axis=alt.Axis(labelAngle=0, labelPadding=10, labelFontSize=12, labelColor="#163A59"),
        ),
        xOffset=alt.XOffset("Jalon:N", sort=metric_cols),
        y=alt.Y(
            "Cas:Q",
            title=None,
            axis=alt.Axis(grid=True, tickMinStep=1, labelFontSize=12, labelColor="#526273"),
            scale=alt.Scale(nice=True, zero=True),
        ),
        color=alt.Color(
            "Jalon:N",
            sort=metric_cols,
            scale=color_scale,
            legend=alt.Legend(title=None, orient="top", direction="horizontal", labelFontSize=12, symbolType="square"),
        ),
        tooltip=[
            alt.Tooltip("Mois:N", title="Mois"),
            alt.Tooltip("Jalon:N", title="Jalon"),
            alt.Tooltip("Cas:Q", title="Cas", format=".0f"),
        ],
    )

    bars = base.mark_bar(size=22, cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
    labels = base.mark_text(
        dy=-10,
        font="Sora",
        fontSize=11,
        fontWeight="bold",
        color="#163A59",
    ).encode(text=alt.Text("Cas:Q", format=".0f"))

    chart = (
        (bars + labels)
        .properties(height=320)
        .configure_view(strokeOpacity=0)
        .configure_axis(domain=False, gridColor="#E6EEF6", tickColor="#E6EEF6", titleColor="#163A59")
        .configure_legend(labelColor="#163A59")
    )

    st.altair_chart(chart, use_container_width=True)
    st.caption("Lecture mensuelle : bleu = mises à jour vigilance, orange = dernières revues, vert = prochaines revues.")


def normalize_analysis_category(series: pd.Series) -> pd.Series:
    return series.fillna("Non renseigné").astype(str).replace({"": "Non renseigné"})


def clear_analysis_focus() -> None:
    for key in [
        "analysis_focus_row_label",
        "analysis_focus_row_value",
        "analysis_focus_col_label",
        "analysis_focus_col_value",
        "analysis_focus_source",
        "analysis_focus_selection",
    ]:
        st.session_state.pop(key, None)


def set_analysis_focus(
    *,
    row_label: str | None = None,
    row_value: str | None = None,
    col_label: str | None = None,
    col_value: str | None = None,
    source: str | None = None,
) -> None:
    if row_label is not None:
        st.session_state["analysis_focus_row_label"] = row_label
        st.session_state["analysis_focus_row_value"] = row_value
    if col_label is not None:
        st.session_state["analysis_focus_col_label"] = col_label
        st.session_state["analysis_focus_col_value"] = col_value
    if source is not None:
        st.session_state["analysis_focus_source"] = source


def validate_analysis_focus(
    df: pd.DataFrame,
    row_col: str,
    row_label: str,
    col_col: str | None,
    col_label: str | None,
) -> None:
    row_value = st.session_state.get("analysis_focus_row_value")
    row_label_state = st.session_state.get("analysis_focus_row_label")
    if row_label_state != row_label:
        st.session_state.pop("analysis_focus_row_label", None)
        st.session_state.pop("analysis_focus_row_value", None)
    elif row_value is not None:
        valid_row_values = set(normalize_analysis_category(df.get(row_col, pd.Series(dtype='object'))).unique().tolist())
        if str(row_value) not in valid_row_values:
            st.session_state.pop("analysis_focus_row_label", None)
            st.session_state.pop("analysis_focus_row_value", None)

    if not col_col or not col_label:
        st.session_state.pop("analysis_focus_col_label", None)
        st.session_state.pop("analysis_focus_col_value", None)
    else:
        col_value = st.session_state.get("analysis_focus_col_value")
        col_label_state = st.session_state.get("analysis_focus_col_label")
        if col_label_state != col_label:
            st.session_state.pop("analysis_focus_col_label", None)
            st.session_state.pop("analysis_focus_col_value", None)
        elif col_value is not None:
            valid_col_values = set(normalize_analysis_category(df.get(col_col, pd.Series(dtype='object'))).unique().tolist())
            if str(col_value) not in valid_col_values:
                st.session_state.pop("analysis_focus_col_label", None)
                st.session_state.pop("analysis_focus_col_value", None)


def build_analysis_focus_dataset(
    df: pd.DataFrame,
    row_col: str | None = None,
    row_value: str | None = None,
    row_label: str | None = None,
    column_col: str | None = None,
    column_value: str | None = None,
    column_label: str | None = None,
) -> pd.DataFrame:
    detail = df.copy()
    focus_parts: list[str] = []

    if row_col and row_value not in {None, "", "Tous"}:
        detail = detail[normalize_analysis_category(detail.get(row_col, pd.Series(index=detail.index, dtype='object'))) == str(row_value)]
        focus_parts.append(f"{row_label or row_col} = {row_value}")

    if column_col and column_value not in {None, "", "Tous"}:
        detail = detail[normalize_analysis_category(detail.get(column_col, pd.Series(index=detail.index, dtype='object'))) == str(column_value)]
        focus_parts.append(f"{column_label or column_col} = {column_value}")

    detail = detail.copy()
    detail["Motif de présence"] = " | ".join(focus_parts) if focus_parts else "Périmètre filtré"
    detail_columns = [
        "SIREN",
        "Dénomination",
        "Vigilance",
        "Risque",
        SOC_COL,
        "Pays de résidence",
        "Segment",
        "Produit(service) principal",
        "Canal d’opérations principal 12 mois",
        "Statut EDD",
        "Analyste",
        "Valideur",
        "Date dernière revue",
        "Motif de présence",
    ]
    detail_columns = [c for c in detail_columns if c in detail.columns]
    return detail[detail_columns]


def render_analysis_kpis(df: pd.DataFrame, full_scope_df: pd.DataFrame | None = None) -> None:
    total_clients = int(len(df))
    scope_total = int(len(full_scope_df)) if full_scope_df is not None else total_clients
    part_portefeuille = (total_clients / scope_total) if scope_total else 0.0

    justificatifs_incomplets = int(
        df.get("Flag justificatif complet", pd.Series(index=df.index, dtype="string"))
        .astype("string")
        .fillna("")
        .ne("Oui")
        .sum()
    )
    sans_prochaine_revue = int(
        df.get("Date prochaine revue", pd.Series(index=df.index, dtype="datetime64[ns]"))
        .isna()
        .sum()
    )
    revue_trop_ancienne = int(
        df.get("Alerte revue trop ancienne", pd.Series(index=df.index, dtype="int64"))
        .fillna(0)
        .astype(int)
        .sum()
    )
    cross_border_eleve = int(
        df.get("Alerte cross-border élevé", pd.Series(index=df.index, dtype="int64"))
        .fillna(0)
        .astype(int)
        .sum()
    )
    cash_intensite_elevee = int(
        df.get("Alerte cash intensité élevée", pd.Series(index=df.index, dtype="int64"))
        .fillna(0)
        .astype(int)
        .sum()
    )
    vigilance_renforcee = int(
        df.get("Vigilance", pd.Series(index=df.index, dtype="string"))
        .astype("string")
        .isin(CRITICAL_VIGILANCE)
        .sum()
    )
    risque_avere = int(
        df.get("Risque", pd.Series(index=df.index, dtype="string"))
        .astype("string")
        .eq("Risque avéré")
        .sum()
    )

    cards = [
        ("Clients", f"{total_clients:,}".replace(",", " "), "Périmètre analysé", ""),
        ("Part du portefeuille", f"{part_portefeuille:.1%}".replace(".", ","), "Poids du périmètre", ""),
        ("Vigilance renforcée", f"{vigilance_renforcee:,}".replace(",", " "), "Élevée + critique", " is-alert"),
        ("Risque avéré", f"{risque_avere:,}".replace(",", " "), "Clients en risque avéré", " is-alert"),
        ("Justificatifs incomplets", f"{justificatifs_incomplets:,}".replace(",", " "), "Documents à compléter", ""),
        ("Sans prochaine revue", f"{sans_prochaine_revue:,}".replace(",", " "), "Revue non planifiée", ""),
        ("Revue trop ancienne", f"{revue_trop_ancienne:,}".replace(",", " "), "Suivi à mettre à jour", ""),
        ("Cross-border élevé", f"{cross_border_eleve:,}".replace(",", " "), "Exposition élevée", ""),
        ("Cash intensité élevée", f"{cash_intensite_elevee:,}".replace(",", " "), "Usage cash élevé", ""),
    ]

    st.markdown('<h3 class="cm-section-title">Bandeau de synthèse</h3>', unsafe_allow_html=True)
    st.markdown(
        "<div class='cm-kpi-band'>"
        + "".join(
            f"<div class='cm-kpi-card{extra_class}'><div class='cm-kpi-label'>{escape(label)}</div><div class='cm-kpi-value'>{escape(value)}</div><div class='cm-kpi-sub'>{escape(sub)}</div></div>"
            for label, value, sub, extra_class in cards
        )
        + "</div>",
        unsafe_allow_html=True,
    )

    if total_clients and "Vigilance Date de mise à jour" in df.columns:
        last_update = pd.to_datetime(df["Vigilance Date de mise à jour"], errors="coerce").max()
        if pd.notna(last_update):
            st.markdown(
                f"<div class='cm-kpi-note'>Dernière mise à jour vigilance visible : <strong>{last_update.strftime('%d/%m/%Y')}</strong>. Les indicateurs sont regroupés dans ce bandeau ; le tableau d’analyse présente uniquement les dimensions de lecture.</div>",
                unsafe_allow_html=True,
            )


def format_table_for_display(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    for col in output.columns:
        if pd.api.types.is_datetime64_any_dtype(output[col]):
            output[col] = output[col].dt.strftime("%d/%m/%Y")
            continue
        if col.startswith("%"):
            output[col] = output[col].map(lambda x: "" if pd.isna(x) else f"{float(x):.1%}")
            continue
        if pd.api.types.is_float_dtype(output[col]):
            non_null = output[col].dropna()
            if non_null.empty:
                continue
            if np.allclose(non_null % 1, 0):
                output[col] = output[col].map(lambda x: "" if pd.isna(x) else f"{int(round(float(x))):,}".replace(",", " "))
            else:
                output[col] = output[col].map(lambda x: "" if pd.isna(x) else f"{float(x):,.1f}".replace(",", " ").replace(".", ","))
        elif pd.api.types.is_integer_dtype(output[col]):
            output[col] = output[col].map(lambda x: "" if pd.isna(x) else f"{int(x):,}".replace(",", " "))
    return output


def render_analysis_main_table(df: pd.DataFrame, selected_row_idx: int | None = None) -> None:
    if df is None or df.empty:
        st.info("Aucune donnée à afficher.")
        return

    display_df = format_table_for_display(df)
    html = ["<div class='cm-analysis-main-wrap'><table class='cm-analysis-main-table'><thead><tr>"]
    for col in display_df.columns:
        header_classes = []
        if str(col) == "Alertes de gouvernance (calculé)":
            header_classes.append("cm-calculated-col")
        header_class_attr = f" class='{' '.join(header_classes)}'" if header_classes else ""
        html.append(f"<th{header_class_attr}>{escape(str(col))}</th>")
    html.append("</tr></thead><tbody>")

    for row_idx, row in display_df.iterrows():
        row_class = " class='cm-row-selected'" if selected_row_idx is not None and row_idx == int(selected_row_idx) else ""
        html.append(f"<tr{row_class}>")
        for idx, col in enumerate(display_df.columns):
            value = row[col]
            classes = []
            original_value = df.iloc[row_idx][col] if col in df.columns else value
            if idx == 0:
                classes.append("cm-first-col")
            if str(col) == "Alertes de gouvernance (calculé)":
                classes.append("cm-calculated-col")
            if isinstance(original_value, (int, float, np.integer, np.floating)) and not isinstance(original_value, bool):
                classes.append("cm-number")
            class_attr = f" class='{' '.join(classes)}'" if classes else ""
            rendered = "" if pd.isna(value) else escape(str(value))
            html.append(f"<td{class_attr}>{rendered}</td>")
        html.append("</tr>")

    html.append("</tbody></table></div>")
    st.markdown("".join(html), unsafe_allow_html=True)



ANALYSIS_FILTER_COLUMNS: list[tuple[str, str]] = [
    ("Vigilance", "Vigilance"),
    ("Risque", "Risque"),
    ("EDD", "Statut EDD"),
    ("Segment", "Segment"),
    ("Pays", "Pays de résidence"),
    ("Produit", "Produit(service) principal"),
    ("Canal", "Canal d’opérations principal 12 mois"),
    ("Analyste", "Analyste"),
    ("Valideur", "Valideur"),
]


@st.cache_data(show_spinner=False)
def build_unified_analysis_table(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    group_labels = [label for label, _ in ANALYSIS_FILTER_COLUMNS]
    if df is None or df.empty:
        return pd.DataFrame(columns=group_labels), ""

    work = df.copy()
    for label, source in ANALYSIS_FILTER_COLUMNS:
        work[label] = normalize_analysis_category(work.get(source, pd.Series(index=work.index, dtype="object")))

    work["cm_client_key"] = work[SOC_COL].astype(str) + "|" + work["SIREN"].astype(str)
    grouped = (
        work.groupby(group_labels, dropna=False)
        .agg(__sort_clients=("cm_client_key", "nunique"))
        .reset_index()
        .sort_values("__sort_clients", ascending=False, kind="stable")
        .drop(columns=["__sort_clients"])
        .reset_index(drop=True)
    )
    caption = "Le tableau d’analyse présente uniquement les dimensions de lecture ; les indicateurs sont portés par le bandeau de synthèse."
    return grouped, caption


def apply_unified_analysis_table_controls(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    work = df.copy().reset_index(drop=True)
    text_cols = [label for label, _ in ANALYSIS_FILTER_COLUMNS if label in work.columns]

    control_cols = st.columns([1.8, 1.35, 1.1, 0.85])
    with control_cols[0]:
        search_value = st.text_input(
            "Recherche",
            value=st.session_state.get("analysis_table_search", ""),
            key="analysis_table_search",
            placeholder="Rechercher une valeur dans le tableau…",
        )
    sort_options = [c for c in work.columns if c not in text_cols] or list(work.columns)
    default_sort = "Clients" if "Clients" in sort_options else (sort_options[0] if sort_options else work.columns[0])
    if st.session_state.get("analysis_table_sort_by") not in sort_options:
        st.session_state["analysis_table_sort_by"] = default_sort
    with control_cols[1]:
        sort_by = st.selectbox(
            "Trier par",
            options=sort_options,
            index=sort_options.index(st.session_state.get("analysis_table_sort_by", default_sort)),
            key="analysis_table_sort_by",
        )
    order_options = ["Décroissant", "Croissant"]
    if st.session_state.get("analysis_table_sort_order") not in order_options:
        st.session_state["analysis_table_sort_order"] = "Décroissant"
    with control_cols[2]:
        sort_order = st.selectbox(
            "Ordre",
            options=order_options,
            index=order_options.index(st.session_state.get("analysis_table_sort_order", "Décroissant")),
            key="analysis_table_sort_order",
        )
    with control_cols[3]:
        top_n = st.number_input(
            "Top N",
            min_value=0,
            max_value=max(len(work), 1),
            value=min(int(st.session_state.get("analysis_table_top_n", min(len(work), 20))), max(len(work), 1)),
            step=1,
            key="analysis_table_top_n",
            help="0 = toutes les lignes",
        )

    if search_value:
        mask = pd.Series(False, index=work.index)
        for col in text_cols:
            mask = mask | work[col].astype(str).str.contains(str(search_value), case=False, na=False)
        work = work[mask]

    ascending = sort_order == "Croissant"
    work = work.sort_values(sort_by, ascending=ascending, kind="stable")
    if int(top_n) > 0:
        work = work.head(int(top_n))
    return work.reset_index(drop=True)


def build_analysis_focus_dataset_from_selection(
    df: pd.DataFrame,
    selection: list[dict[str, object]] | dict[str, object] | None,
) -> tuple[pd.DataFrame, list[str]]:
    if not selection:
        return pd.DataFrame(), []

    selections = selection if isinstance(selection, list) else [selection]
    base = df.copy()
    detail_frames: list[pd.DataFrame] = []
    focus_parts: list[str] = []

    for item in selections:
        row_mask = pd.Series(True, index=base.index)
        local_parts: list[str] = []
        for label, source in ANALYSIS_FILTER_COLUMNS:
            if label not in item:
                continue
            raw_value = item.get(label)
            value = "Non renseigné" if pd.isna(raw_value) or str(raw_value).strip() == "" else str(raw_value)
            row_mask = row_mask & (
                normalize_analysis_category(base.get(source, pd.Series(index=base.index, dtype="object"))) == value
            )
            local_parts.append(f"{label} = {value}")

        if not row_mask.any():
            continue

        motif = " | ".join(local_parts) if local_parts else "Périmètre filtré"
        row_detail = base.loc[row_mask].copy()
        row_detail["Motif de présence"] = motif
        detail_frames.append(row_detail)
        focus_parts.append(motif)

    if not detail_frames:
        return pd.DataFrame(), []

    detail = pd.concat(detail_frames, ignore_index=True)
    detail["cm_client_key"] = detail[SOC_COL].astype(str) + "|" + detail["SIREN"].astype(str)

    detail_columns = [
        "SIREN",
        "Dénomination",
        "Vigilance",
        "Risque",
        SOC_COL,
        "Pays de résidence",
        "Segment",
        "Produit(service) principal",
        "Canal d’opérations principal 12 mois",
        "Statut EDD",
        "Analyste",
        "Valideur",
        "Date dernière revue",
        "Motif de présence",
    ]
    detail_columns = [c for c in detail_columns if c in detail.columns]

    aggregate = {col: "first" for col in detail_columns if col != "Motif de présence"}
    aggregate["Motif de présence"] = lambda s: " || ".join(dict.fromkeys(str(v) for v in s if pd.notna(v) and str(v).strip()))
    detail = (
        detail[["cm_client_key"] + detail_columns]
        .groupby("cm_client_key", as_index=False)
        .agg(aggregate)
        .drop(columns=["cm_client_key"], errors="ignore")
    )
    return detail[detail_columns], focus_parts




def build_existing_review_dates_dataset(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=[SOC_COL, "SIREN", "Dénomination", "Régime de vigilance", "Date prochaine revue"])

    work = df.copy()
    work["Date prochaine revue"] = pd.to_datetime(
        work.get("Date prochaine revue", pd.Series(index=work.index, dtype="datetime64[ns]")),
        errors="coerce",
        dayfirst=True,
    )
    work = work.dropna(subset=["Date prochaine revue"]).copy()
    if work.empty:
        return pd.DataFrame(columns=[SOC_COL, "SIREN", "Dénomination", "Régime de vigilance", "Date prochaine revue"])

    regimes = work.apply(lambda row: review_vigilance_regime(row)[0], axis=1)
    work["Régime de vigilance"] = regimes
    cols = [c for c in [SOC_COL, "SIREN", "Dénomination", "Régime de vigilance", "Date prochaine revue"] if c in work.columns]
    work = work[cols].drop_duplicates(subset=[c for c in [SOC_COL, "SIREN"] if c in cols], keep="last")
    return work


def render_analysis_review_dates_from_base(df: pd.DataFrame) -> None:
    st.markdown('<h3 class="cm-section-title">Planification des revues</h3>', unsafe_allow_html=True)
    st.caption("Cette vue reprend uniquement les dates de prochaine revue déjà présentes dans le fichier 01, sur le périmètre filtré en haut de l’écran Analyse.")

    schedule_df = build_existing_review_dates_dataset(df)
    if schedule_df.empty:
        st.info("Aucune date de prochaine revue n’est disponible dans le fichier 01 sur le périmètre filtré.")
        return

    chart_df = build_review_schedule_chart_table(schedule_df)
    render_review_schedule_chart(chart_df)

    available = int(schedule_df["Date prochaine revue"].notna().sum())
    missing = int(len(df) - available)
    cards = [
        ("SIREN datés", f"{available:,}".replace(",", " "), "Dates issues du fichier 01", ""),
        ("Sans date", f"{missing:,}".replace(",", " "), "Aucune prochaine revue dans le fichier 01", " is-alert" if missing > 0 else ""),
    ]
    st.markdown(
        "<div class='cm-kpi-band'>"
        + "".join(
            f"<div class='cm-kpi-card{extra_class}'><div class='cm-kpi-label'>{escape(label)}</div><div class='cm-kpi-value'>{escape(value)}</div><div class='cm-kpi-sub'>{escape(sub)}</div></div>"
            for label, value, sub, extra_class in cards
        )
        + "</div>",
        unsafe_allow_html=True,
    )



def render_analysis_screen(portfolio: pd.DataFrame, indicators: pd.DataFrame) -> None:
    render_home_hero("Analyse")
    nav = render_primary_navigation("analysis")
    if nav == "portfolio":
        open_portfolio_view()
        st.rerun()
    if nav == "review_dates":
        open_review_dates_view()
        st.rerun()
    if nav == "review_simulations":
        open_review_simulations_view()
        st.rerun()
    if nav == "evolution":
        open_evolution_view()
        st.rerun()

    top_left, top_right = st.columns([5.4, 1.2])
    with top_left:
        st.markdown('<h3 class="cm-section-title">Analyse des indicateurs d’alerte</h3>', unsafe_allow_html=True)
        st.caption("Le haut de l’écran est consacré aux indicateurs d’alerte : filtres, synthèse, répartitions et concentrations. Le bloc ‘Indicateurs les plus contributifs’ est conservé dans sa présentation de lecture actuelle.")
    with top_right:
        if st.button("Réinitialiser", type="secondary", key="analysis_reset_all"):
            reset_filters()
            for key in [
                "analysis_selected_idx_analysis_main",
                "analysis_table_search",
                "analysis_table_sort_by",
                "analysis_table_sort_order",
                "analysis_table_top_n",
                "analysis_filter_indicator_name",
                "analysis_filter_indicator_status",
                "analysis_filter_indicator_family",
                "analysis_filter_indicator_freshness",
                "analysis_top_sort_mode",
            ]:
                st.session_state.pop(key, None)
            clear_analysis_focus()
            st.rerun()

    st.markdown('<h3 class="cm-section-title">Filtres</h3>', unsafe_allow_html=True)
    st.caption("La première ligne cadre le portefeuille ; la seconde affine les cas indicateurs. Ces calculs sont propres à l’écran Analyse et n’impactent pas l’écran Portefeuille.")

    dataset_signature = build_dataset_cache_signature()
    analysis_societies_key = tuple(available_societies(portfolio))

    selections: dict[str, str] = {}
    filter_cols = st.columns(5)
    for idx, label in enumerate(ANALYSIS_PORTFOLIO_FILTER_LABELS):
        column = FILTER_MAPPING[label]
        options = ["Tous"] + non_empty_sorted(portfolio[column].unique()) if column in portfolio.columns else ["Tous"]
        state_key = "filter_" + label
        if st.session_state.get(state_key) not in options:
            st.session_state[state_key] = "Tous"
        with filter_cols[idx % 5]:
            selections[label] = st.selectbox(label, options=options, key=state_key)
        if idx % 5 == 4 and idx < len(ANALYSIS_PORTFOLIO_FILTER_LABELS) - 1:
            filter_cols = st.columns(5)

    portfolio_filters_key = normalize_filter_cache_key(selections, ANALYSIS_PORTFOLIO_FILTER_LABELS)
    filtered_portfolio, analysis_base = get_analysis_base_for_portfolio_filters_cached(
        dataset_signature,
        ANALYSIS_SCREEN_CACHE_VERSION,
        analysis_societies_key,
        portfolio_filters_key,
    )
    if filtered_portfolio.empty:
        st.warning("Aucun client ne correspond au périmètre société + filtres sélectionnés.")
        return

    indicator_cols = st.columns(4)
    indicator_options = ["Tous"] + non_empty_sorted(analysis_base["Indicateur"].astype(str).unique()) if not analysis_base.empty else ["Tous"]
    if st.session_state.get("analysis_filter_indicator_name") not in indicator_options:
        st.session_state["analysis_filter_indicator_name"] = "Tous"
    with indicator_cols[0]:
        indicator_value = st.selectbox("Indicateur", options=indicator_options, key="analysis_filter_indicator_name")

    available_statuses = [status for status in ANALYSIS_STATUS_ORDER if not analysis_base.empty and analysis_base["Statut"].astype(str).eq(status).any()]
    status_options = ["Tous"] + available_statuses if available_statuses else ["Tous"]
    if st.session_state.get("analysis_filter_indicator_status") not in status_options:
        st.session_state["analysis_filter_indicator_status"] = "Tous"
    with indicator_cols[1]:
        status_value = st.selectbox(
            "Statut indicateur",
            options=status_options,
            key="analysis_filter_indicator_status",
            format_func=lambda value: "Tous" if value == "Tous" else analysis_status_ui_label(value),
        )

    family_options = ["Tous"] + [family for family in ANALYSIS_FAMILY_ORDER if not analysis_base.empty and analysis_base["Famille indicateur"].astype(str).eq(family).any()]
    if st.session_state.get("analysis_filter_indicator_family") not in family_options:
        st.session_state["analysis_filter_indicator_family"] = "Tous"
    with indicator_cols[2]:
        family_value = st.selectbox("Famille indicateur", options=family_options, key="analysis_filter_indicator_family")

    freshness_options = ["Tous"] + [bucket for bucket in ANALYSIS_FRESHNESS_ORDER if not analysis_base.empty and analysis_base["Fraîcheur indicateur"].astype(str).eq(bucket).any()]
    if st.session_state.get("analysis_filter_indicator_freshness") not in freshness_options:
        st.session_state["analysis_filter_indicator_freshness"] = "Tous"
    with indicator_cols[3]:
        freshness_value = st.selectbox("Fraîcheur", options=freshness_options, key="analysis_filter_indicator_freshness")

    indicator_filters = {
        "Indicateur": indicator_value,
        "Statut": status_value,
        "Famille": family_value,
        "Fraîcheur": freshness_value,
    }
    indicator_filters_key = normalize_filter_cache_key(indicator_filters, ANALYSIS_INDICATOR_FILTER_KEYS)

    current_sort_mode = st.session_state.get("analysis_top_sort_mode", "Nb")
    if current_sort_mode not in ANALYSIS_TOP_SORT_OPTIONS:
        current_sort_mode = "Nb"

    compute_key = str((
        dataset_signature,
        ANALYSIS_SCREEN_CACHE_VERSION,
        analysis_societies_key,
        portfolio_filters_key,
        indicator_filters_key,
    ))
    seen_compute_keys = set(st.session_state.get("analysis_screen_compute_seen_keys", set()))
    should_show_compute_status = compute_key not in seen_compute_keys

    payload: dict[str, object]
    if should_show_compute_status:
        status_anchor = st.container()
        if hasattr(st, "status"):
            with status_anchor:
                with st.status("Les indicateurs sont en cours de calcul…", expanded=True) as status_box:
                    counter_placeholder = st.empty()
                    progress_bar = st.progress(1)
                    counter_placeholder.info("Calcul 0/9 — Initialisation de l’écran Analyse")
                    time.sleep(0.12)

                    def progress_callback(step_number: int, total_steps: int, label: str) -> None:
                        progress_bar.progress(max(5, int((step_number / total_steps) * 100)))
                        counter_placeholder.info(f"Calcul {step_number}/{total_steps} — {label}")
                        status_box.update(label=f"Les indicateurs sont en cours de calcul… {label}", state="running", expanded=True)

                    payload = build_analysis_screen_payload(
                        dataset_signature,
                        ANALYSIS_SCREEN_CACHE_VERSION,
                        analysis_societies_key,
                        portfolio_filters_key,
                        indicator_filters_key,
                        sort_mode=current_sort_mode,
                        progress_callback=progress_callback,
                    )
                    progress_bar.progress(100)
                    counter_placeholder.success("Calcul terminé. Les compteurs et classements de l’écran Analyse sont prêts.")
                    status_box.update(label="Calcul des indicateurs terminé", state="complete", expanded=False)
        else:
            with status_anchor:
                st.info("Les indicateurs sont en cours de calcul…")
                progress_bar = st.progress(1)
                counter_placeholder = st.empty()
                counter_placeholder.info("Calcul 0/9 — Initialisation de l’écran Analyse")
                time.sleep(0.12)

                def progress_callback(step_number: int, total_steps: int, label: str) -> None:
                    progress_bar.progress(max(5, int((step_number / total_steps) * 100)))
                    counter_placeholder.info(f"Calcul {step_number}/{total_steps} — {label}")

                payload = build_analysis_screen_payload(
                    dataset_signature,
                    ANALYSIS_SCREEN_CACHE_VERSION,
                    analysis_societies_key,
                    portfolio_filters_key,
                    indicator_filters_key,
                    sort_mode=current_sort_mode,
                    progress_callback=progress_callback,
                )
                progress_bar.progress(100)
                counter_placeholder.success("Calcul terminé. Les compteurs et classements de l’écran Analyse sont prêts.")
        seen_compute_keys.add(compute_key)
        st.session_state["analysis_screen_compute_seen_keys"] = seen_compute_keys
    else:
        payload = build_analysis_screen_payload(
            dataset_signature,
            ANALYSIS_SCREEN_CACHE_VERSION,
            analysis_societies_key,
            portfolio_filters_key,
            indicator_filters_key,
            sort_mode=current_sort_mode,
        )

    filtered_portfolio = payload["filtered_portfolio"]
    analysis_base = payload["analysis_base"]
    filtered_indicators = payload["filtered_indicators"]
    analysis_client_scope = payload["analysis_client_scope"]
    status_distribution = payload["status_distribution"]
    family_distribution = payload["family_distribution"]
    freshness_distribution = payload["freshness_distribution"]
    analysis_top_tables = payload["top_tables"]
    indicator_table = payload["indicator_table"]

    if filtered_portfolio.empty:
        st.warning("Aucun client ne correspond au périmètre société + filtres sélectionnés.")
        return

    if filtered_indicators.empty:
        st.warning("Aucun cas indicateur ne correspond aux filtres d’analyse sélectionnés. Le bandeau, les répartitions et les concentrations reflètent donc un périmètre vide.")

    render_analysis_alert_kpis(filtered_portfolio, analysis_client_scope, filtered_indicators)

    st.divider()
    render_analysis_repartition(
        filtered_indicators,
        status_distribution=status_distribution,
        family_distribution=family_distribution,
        freshness_distribution=freshness_distribution,
    )

    st.divider()
    render_analysis_concentrations(
        filtered_indicators,
        analysis_client_scope,
        precomputed_tables=analysis_top_tables,
        sort_mode=current_sort_mode,
    )

    st.divider()
    render_indicator_contribution_chart(indicator_table)

    analysis_table, _ = build_unified_analysis_table(analysis_client_scope)
    portfolio_filters_export = {label: selections.get(label, "Tous") for label in ANALYSIS_PORTFOLIO_FILTER_LABELS}
    indicator_filters_export = {
        "Indicateur": indicator_value,
        "Statut indicateur": "Tous" if status_value == "Tous" else analysis_status_ui_label(status_value),
        "Famille indicateur": family_value,
        "Fraîcheur": freshness_value,
    }
    active_analysis_top_sort = st.session_state.get("analysis_top_sort_mode", current_sort_mode)
    analysis_committee_excel = build_analysis_committee_pack_excel_bytes(
        selected_societies=list(analysis_societies_key),
        portfolio_filters=portfolio_filters_export,
        indicator_filters=indicator_filters_export,
        sort_mode=active_analysis_top_sort,
        filtered_portfolio=filtered_portfolio,
        filtered_indicators=filtered_indicators,
        analysis_client_scope=analysis_client_scope,
        status_distribution=status_distribution,
        family_distribution=family_distribution,
        freshness_distribution=freshness_distribution,
        top_segment_df=analysis_top_tables.get("Segment / Client", pd.DataFrame()),
        top_pays_df=analysis_top_tables.get("Indicateurs Pays", pd.DataFrame()),
        top_produits_df=analysis_top_tables.get("Indicateurs Produits", pd.DataFrame()),
        top_canaux_df=analysis_top_tables.get("Indicateurs Canal", pd.DataFrame()),
        indicator_table=indicator_table,
        analysis_table=analysis_table,
    )

    analysis_committee_pdf_bytes = None
    analysis_committee_pdf_error = ""
    if REPORTLAB_AVAILABLE:
        try:
            analysis_committee_pdf_bytes = build_analysis_committee_report_pdf_bytes(
                selected_societies=list(analysis_societies_key),
                portfolio_filters=portfolio_filters_export,
                indicator_filters=indicator_filters_export,
                sort_mode=active_analysis_top_sort,
                filtered_portfolio=filtered_portfolio,
                filtered_indicators=filtered_indicators,
                analysis_client_scope=analysis_client_scope,
                status_distribution=status_distribution,
                family_distribution=family_distribution,
                freshness_distribution=freshness_distribution,
                top_segment_df=analysis_top_tables.get("Segment / Client", pd.DataFrame()),
                top_pays_df=analysis_top_tables.get("Indicateurs Pays", pd.DataFrame()),
                top_produits_df=analysis_top_tables.get("Indicateurs Produits", pd.DataFrame()),
                top_canaux_df=analysis_top_tables.get("Indicateurs Canal", pd.DataFrame()),
                indicator_table=indicator_table,
                analysis_table=analysis_table,
            )
        except Exception as exc:
            analysis_committee_pdf_error = str(exc)
    else:
        analysis_committee_pdf_error = PDF_DEPENDENCY_ERROR_MESSAGE

    with st.expander("Préparer votre Comité des Risques", expanded=False):
        st.caption("Exports Comité des Risques de l’écran Analyse : pack Excel multi-onglets et synthèse PDF exécutive adaptés aux alertes du périmètre filtré.")
        export_col_excel, export_col_pdf = st.columns(2)
        with export_col_excel:
            st.download_button(
                label="Pack Comité des Risques (.xlsx)",
                data=analysis_committee_excel,
                file_name=analysis_committee_pack_download_name(list(analysis_societies_key)),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )
        with export_col_pdf:
            if analysis_committee_pdf_bytes is not None and len(analysis_committee_pdf_bytes) > 0:
                st.download_button(
                    label="Rapport Comité des Risques (.pdf)",
                    data=analysis_committee_pdf_bytes,
                    file_name=analysis_committee_report_download_name(list(analysis_societies_key)),
                    mime="application/pdf",
                    use_container_width=True,
                )
            elif analysis_committee_pdf_error:
                st.info(analysis_committee_pdf_error)
            else:
                st.warning("Le PDF n’a pas pu être préparé pour ce périmètre.")

    with st.expander("Lecture détaillée des dimensions", expanded=False):
        render_analysis_panel_header(
            "Tableau d’analyse",
            "Cette table conserve la lecture détaillée par dimensions et permet, par clic, d’alimenter les clients sous-jacents sans modifier les calculs de l’écran Portefeuille.",
        )
        display_analysis_table = apply_unified_analysis_table_controls(analysis_table)
        main_action, selected_main = render_selectable_analysis_table(display_analysis_table, key_prefix="analysis_main", height=520)

        if main_action == "selected" and selected_main:
            st.session_state["analysis_focus_selection"] = selected_main
        elif main_action == "cleared":
            if "analysis_focus_selection" in st.session_state:
                st.session_state.pop("analysis_focus_selection", None)
                st.rerun()

        if analysis_table.empty:
            st.info("Aucune dimension détaillée à afficher sur le périmètre sélectionné.")
        elif display_analysis_table.empty:
            st.info("Aucune ligne ne correspond aux contrôles intégrés du tableau d’analyse.")

        st.divider()
        st.markdown("<div id='clients-sous-jacents'></div>", unsafe_allow_html=True)
        st.markdown('<h3 class="cm-section-title">Clients sous-jacents</h3>', unsafe_allow_html=True)

        focus_selection = st.session_state.get("analysis_focus_selection")
        detail_df, focus_parts = build_analysis_focus_dataset_from_selection(analysis_client_scope, focus_selection)

        focus_bar_left, focus_bar_right = st.columns([6.0, 1.2])
        with focus_bar_left:
            if focus_parts:
                if len(focus_parts) == 1:
                    st.caption("Focus actif : " + focus_parts[0])
                else:
                    preview = " ; ".join(focus_parts[:2])
                    if len(focus_parts) > 2:
                        preview += f" ; +{len(focus_parts) - 2} autre(s) ligne(s)"
                    st.caption(f"Focus actif : {len(focus_parts)} lignes sélectionnées — " + preview)
            else:
                st.caption("Cliquez sur une ou plusieurs lignes du tableau d’analyse pour afficher ici les clients sous-jacents correspondants.")
        with focus_bar_right:
            if focus_parts and st.button("Effacer le focus", type="secondary", key="analysis_clear_focus"):
                clear_analysis_focus()
                st.rerun()

        if detail_df.empty:
            st.info("Aucun client sous-jacent à afficher tant qu’aucun focus n’est sélectionné.")
        else:
            st.caption("Cliquez sur un SIREN pour ouvrir la fiche client sans quitter votre contexte d’analyse.")
            render_clickable_styled_dataframe(
                style_dataframe(detail_df),
                detail_df,
                height=440,
                hide_index=True,
                key_prefix="analysis_detail_clients",
            )

    render_analysis_glossary_expander()


def review_setting_slug(label: str) -> str:
    slug = label.lower()
    slug = slug.replace("é", "e").replace("è", "e").replace("ê", "e")
    slug = slug.replace("à", "a").replace("ù", "u")
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")


def ensure_review_planning_state_defaults() -> None:
    saved_freq_map, saved_cap_map = load_saved_review_planning_settings()
    for label in VIGILANCE_ORDER:
        freq_key = f"review_freq_{review_setting_slug(label)}"
        cap_key = f"review_cap_{review_setting_slug(label)}"
        st.session_state.setdefault(freq_key, int(saved_freq_map.get(label, REVIEW_FREQUENCY_DEFAULTS.get(label, 12))))
        st.session_state.setdefault(cap_key, int(saved_cap_map.get(label, REVIEW_CAPACITY_DEFAULTS.get(label, 10))))


def get_review_planning_settings() -> tuple[dict[str, int], dict[str, int]]:
    ensure_review_planning_state_defaults()
    freq_map: dict[str, int] = {}
    cap_map: dict[str, int] = {}
    for label in VIGILANCE_ORDER:
        freq_key = f"review_freq_{review_setting_slug(label)}"
        cap_key = f"review_cap_{review_setting_slug(label)}"
        freq_map[label] = int(st.session_state.get(freq_key, REVIEW_FREQUENCY_DEFAULTS.get(label, 12)))
        cap_map[label] = int(st.session_state.get(cap_key, REVIEW_CAPACITY_DEFAULTS.get(label, 10)))
    return freq_map, cap_map


def review_table_static_cell(value: object, *, header: bool = False, align: str = "center") -> str:
    bg = PRIMARY_COLOR if header else "#F8FBFF"
    fg = "#FFFFFF" if header else "#163A59"
    weight = 700 if header else 600
    border = "none" if header else "1px solid rgba(22, 58, 89, 0.10)"
    radius = "10px" if header else "10px"
    pad = "0.72rem 0.55rem" if header else "0.78rem 0.55rem"
    size = "0.82rem" if header else "0.9rem"
    return (
        f"<div style='background:{bg}; color:{fg}; border:{border}; border-radius:{radius}; "
        f"padding:{pad}; text-align:{align}; font-weight:{weight}; font-size:{size}; line-height:1.1;'>"
        f"{escape(str(value))}</div>"
    )



def render_review_rule_editor(df: pd.DataFrame) -> tuple[dict[str, int], dict[str, int], bool]:
    ensure_review_planning_state_defaults()
    dist = build_distribution(df, "Vigilance", VIGILANCE_ORDER).rename(columns={"Libellé": "Régime de vigilance"})
    count_map = {row["Régime de vigilance"]: int(row["Nb"]) for _, row in dist.iterrows()}
    share_map = {row["Régime de vigilance"]: float(row["%"] if pd.notna(row["%"] ) else 0.0) for _, row in dist.iterrows()}

    st.markdown('<h3 class="cm-section-title">Règles de planification des revues</h3>', unsafe_allow_html=True)
    st.caption("Fréquence par régime de vigilance + capacité maximale de revues par mois. Si la capacité d’un mois est dépassée, l’excédent est décalé automatiquement sur les mois suivants.")

    with st.form("review_planning_rules_form"):
        header_cols = st.columns([2.9, 0.8, 0.9, 1.35, 1.55])
        headers = ["Régime de vigilance", "Nb", "%", "Fréquence (mois)", "Capacité max / mois"]
        for col, title in zip(header_cols, headers):
            with col:
                st.markdown(review_table_static_cell(title, header=True), unsafe_allow_html=True)

        for regime in VIGILANCE_ORDER:
            freq_key = f"review_freq_{review_setting_slug(regime)}"
            cap_key = f"review_cap_{review_setting_slug(regime)}"
            row_cols = st.columns([2.9, 0.8, 0.9, 1.35, 1.55])
            with row_cols[0]:
                st.markdown(review_table_static_cell(regime, align="left"), unsafe_allow_html=True)
            with row_cols[1]:
                st.markdown(review_table_static_cell(count_map.get(regime, 0)), unsafe_allow_html=True)
            with row_cols[2]:
                st.markdown(review_table_static_cell(f"{share_map.get(regime, 0.0) * 100:.1f}%"), unsafe_allow_html=True)
            with row_cols[3]:
                st.number_input(
                    f"Fréquence {regime}",
                    min_value=1,
                    max_value=60,
                    step=1,
                    key=freq_key,
                    label_visibility="collapsed",
                )
            with row_cols[4]:
                st.number_input(
                    f"Capacité {regime}",
                    min_value=1,
                    max_value=500,
                    step=1,
                    key=cap_key,
                    label_visibility="collapsed",
                )

        recalc = st.form_submit_button("Recalculer le planning", type="primary", use_container_width=True)

    freq_map, cap_map = get_review_planning_settings()
    return freq_map, cap_map, recalc



def review_vigilance_regime(row: pd.Series) -> tuple[str, str]:
    raw_value = str(row.get("Vigilance", "") or "").strip()
    value = raw_value.lower()
    if "critique" in value:
        return "Vigilance Critique", "Régime de vigilance = Critique"
    if "élev" in value or "elev" in value:
        return "Vigilance Élevée", "Régime de vigilance = Élevée"
    if "modér" in value or "moder" in value:
        return "Vigilance Modérée", "Régime de vigilance = Modérée"
    if "allég" in value or "alleg" in value:
        return "Vigilance Allégée", "Régime de vigilance = Allégée"
    if "aucune" in value:
        return "Vigilance Aucune", "Régime de vigilance = Aucune"
    if raw_value in VIGILANCE_ORDER:
        return raw_value, f"Régime de vigilance = {raw_value.replace('Vigilance ', '')}"
    return "Vigilance Aucune", "Régime de vigilance par défaut = Aucune"



def compute_review_base_date(row: pd.Series, today: pd.Timestamp) -> tuple[pd.Timestamp, str]:
    last_review = pd.to_datetime(row.get("Date dernière revue"), errors="coerce")
    if pd.notna(last_review):
        return pd.Timestamp(last_review).normalize(), "Date dernière revue"

    vig_update = pd.to_datetime(row.get("Vigilance Date de mise à jour"), errors="coerce")
    if pd.notna(vig_update):
        return pd.Timestamp(vig_update).normalize(), "Dernière mise à jour vigilance"

    return today.normalize(), "Date du jour"



def shift_date_to_target_month(date_value: pd.Timestamp, target_month: pd.Timestamp) -> pd.Timestamp:
    date_value = pd.Timestamp(date_value).normalize()
    target_month = pd.Timestamp(target_month).normalize().replace(day=1)
    month_end = (target_month + pd.offsets.MonthEnd(0)).normalize()
    day = min(int(date_value.day), int(month_end.day))
    return pd.Timestamp(year=int(target_month.year), month=int(target_month.month), day=day)



def month_offset(start_month: pd.Timestamp, end_month: pd.Timestamp) -> int:
    start_month = pd.Timestamp(start_month)
    end_month = pd.Timestamp(end_month)
    return int((end_month.year - start_month.year) * 12 + (end_month.month - start_month.month))



def smooth_review_schedule(schedule_df: pd.DataFrame, capacity_map: dict[str, int], today: pd.Timestamp) -> pd.DataFrame:
    if schedule_df is None or schedule_df.empty:
        return schedule_df

    schedule = schedule_df.copy()
    schedule["Date prochaine revue"] = pd.NaT
    schedule["Mois théorique"] = ""
    schedule["Mois planifié"] = ""
    schedule["Lissé"] = "Non"
    schedule["Décalage (mois)"] = 0
    schedule["Capacité max / mois"] = 0

    current_month = today.to_period("M").to_timestamp()
    for regime in VIGILANCE_ORDER:
        mask = schedule["Régime de vigilance"].eq(regime)
        if not mask.any():
            continue
        capacity = max(int(capacity_map.get(regime, REVIEW_CAPACITY_DEFAULTS.get(regime, 10))), 1)
        bucket_usage: dict[pd.Timestamp, int] = {}
        group = schedule.loc[mask].sort_values(["Date prochaine revue théorique", "Date de base", "SIREN"], kind="stable")
        for idx, row in group.iterrows():
            theoretical = pd.to_datetime(row.get("Date prochaine revue théorique"), errors="coerce")
            if pd.isna(theoretical):
                theoretical = today.normalize()
            base_month = theoretical.to_period("M").to_timestamp()
            candidate_month = base_month if base_month >= current_month else current_month
            source_month = candidate_month
            while bucket_usage.get(candidate_month, 0) >= capacity:
                candidate_month = (candidate_month + pd.DateOffset(months=1)).to_period("M").to_timestamp()
            planned_date = shift_date_to_target_month(theoretical, candidate_month)
            bucket_usage[candidate_month] = bucket_usage.get(candidate_month, 0) + 1

            schedule.at[idx, "Date prochaine revue"] = planned_date
            schedule.at[idx, "Mois théorique"] = theoretical.to_period("M").strftime("%Y-%m")
            schedule.at[idx, "Mois planifié"] = pd.Timestamp(candidate_month).strftime("%Y-%m")
            schedule.at[idx, "Lissé"] = "Oui" if candidate_month != source_month else "Non"
            schedule.at[idx, "Décalage (mois)"] = month_offset(source_month, candidate_month)
            schedule.at[idx, "Capacité max / mois"] = capacity

    planned_dates = pd.to_datetime(schedule["Date prochaine revue"], errors="coerce")
    delta_days = (planned_dates - today).dt.days
    schedule["Statut planning"] = np.select(
        [delta_days < 0, delta_days <= 30, delta_days <= 90],
        ["En retard", "À 30 jours", "31-90 jours"],
        default="Au-delà de 90 jours",
    )
    schedule = schedule.sort_values(["Date prochaine revue", "Régime de vigilance", SOC_COL, "SIREN"], kind="stable").reset_index(drop=True)
    return schedule



def build_review_schedule(df: pd.DataFrame, freq_map: dict[str, int], capacity_map: dict[str, int], today: pd.Timestamp | None = None) -> pd.DataFrame:
    if today is None:
        today = pd.Timestamp.today().normalize()
    if df is None or df.empty:
        return pd.DataFrame(columns=[SOC_COL, "SIREN", "Régime de vigilance", "Date prochaine revue"]) 

    rows: list[dict[str, object]] = []
    for _, row in df.iterrows():
        regime, reason = review_vigilance_regime(row)
        base_date, base_source = compute_review_base_date(row, today)
        months = int(freq_map.get(regime, REVIEW_FREQUENCY_DEFAULTS.get(regime, 12)))
        theoretical = (base_date + pd.DateOffset(months=months)).normalize()
        rows.append(
            {
                SOC_COL: row.get(SOC_COL),
                "SIREN": row.get("SIREN"),
                "Dénomination": row.get("Dénomination"),
                "Régime de vigilance": regime,
                "Règle appliquée": reason,
                "Fréquence (mois)": months,
                "Date de base": base_date,
                "Source date de base": base_source,
                "Date prochaine revue théorique": theoretical,
                "Vigilance": row.get("Vigilance"),
                "Risque": row.get("Risque"),
            }
        )

    schedule = pd.DataFrame(rows)
    if schedule.empty:
        return schedule
    return smooth_review_schedule(schedule, capacity_map, today)



def build_review_schedule_chart_table(schedule_df: pd.DataFrame, today: pd.Timestamp | None = None) -> pd.DataFrame:
    if today is None:
        today = pd.Timestamp.today().normalize()
    if schedule_df is None or schedule_df.empty:
        return pd.DataFrame(columns=["Mois"] + VIGILANCE_ORDER)

    work = schedule_df.copy()
    due = pd.to_datetime(work["Date prochaine revue"], errors="coerce")
    current_month = today.to_period("M").to_timestamp()
    month_bucket = due.dt.to_period("M").dt.to_timestamp()
    month_bucket = month_bucket.where(month_bucket >= current_month, current_month)
    work["Mois"] = month_bucket

    max_month = month_bucket.max()
    if pd.isna(max_month):
        max_month = current_month
    horizon_end = max(current_month + pd.DateOffset(months=11), pd.Timestamp(max_month))
    month_index = pd.date_range(current_month, horizon_end, freq="MS")

    grouped = (
        work.groupby(["Mois", "Régime de vigilance"]).size().unstack(fill_value=0).reindex(month_index, fill_value=0)
    )
    for col in VIGILANCE_ORDER:
        if col not in grouped.columns:
            grouped[col] = 0
    grouped = grouped[VIGILANCE_ORDER].reset_index().rename(columns={"index": "Mois"})
    grouped["Mois"] = pd.to_datetime(grouped["Mois"]).dt.strftime("%Y-%m")
    return grouped



def render_review_schedule_chart(chart_df: pd.DataFrame) -> None:
    if chart_df is None or chart_df.empty:
        st.info("Aucune revue planifiée n'est disponible sur le périmètre filtré.")
        return

    metric_cols = VIGILANCE_ORDER
    chart_df = chart_df.copy()
    for col in metric_cols:
        chart_df[col] = pd.to_numeric(chart_df[col], errors="coerce").fillna(0).round(0).astype(int)
    chart_df["Total"] = chart_df[metric_cols].sum(axis=1)

    month_order = chart_df["Mois"].astype(str).tolist()
    melted = chart_df.melt(id_vars=["Mois"], value_vars=metric_cols, var_name="Régime de vigilance", value_name="Cas")
    color_scale = alt.Scale(
        domain=metric_cols,
        range=["#BF2424", "#F28C28", "#EAAA08", "#5E8FC7", "#163A59"],
    )

    bars = alt.Chart(melted).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
        x=alt.X("Mois:N", sort=month_order, title=None, axis=alt.Axis(labelAngle=0, labelPadding=10, labelFontSize=12, labelColor="#163A59")),
        y=alt.Y("Cas:Q", title=None, axis=alt.Axis(grid=True, tickMinStep=1, labelFontSize=12, labelColor="#526273"), stack=True),
        color=alt.Color("Régime de vigilance:N", sort=metric_cols, scale=color_scale, legend=alt.Legend(title=None, orient="top", direction="horizontal", labelFontSize=12, symbolType="square")),
        tooltip=[
            alt.Tooltip("Mois:N", title="Mois"),
            alt.Tooltip("Régime de vigilance:N", title="Régime"),
            alt.Tooltip("Cas:Q", title="Cas", format=".0f"),
        ],
    )

    totals = alt.Chart(chart_df).mark_text(dy=-10, font="Sora", fontSize=11, fontWeight="bold", color="#163A59").encode(
        x=alt.X("Mois:N", sort=month_order),
        y=alt.Y("Total:Q"),
        text=alt.Text("Total:Q", format=".0f"),
    )

    chart = (
        (bars + totals)
        .properties(height=330)
        .configure_view(strokeOpacity=0)
        .configure_axis(domain=False, gridColor="#E6EEF6", tickColor="#E6EEF6", titleColor="#163A59")
        .configure_legend(labelColor="#163A59")
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption("Chaque barre empilée représente la charge mensuelle planifiée après lissage. Les dossiers au-delà de la capacité d’un mois sont décalés sur les mois suivants dans le même régime de vigilance.")



def render_review_schedule_kpis(schedule_df: pd.DataFrame) -> None:
    if schedule_df is None or schedule_df.empty:
        st.info("Aucune revue n'est disponible sur le périmètre filtré.")
        return

    today = pd.Timestamp.today().normalize()
    planned_dates = pd.to_datetime(schedule_df["Date prochaine revue"], errors="coerce")
    current_month = today.to_period("M").strftime("%Y-%m")
    this_month = planned_dates.dt.to_period("M").astype(str).eq(current_month)
    cards = [
        ("SIREN planifiés", f"{len(schedule_df):,}".replace(",", " "), "Portefeuille courant", ""),
        ("Revues ce mois", f"{int(this_month.sum()):,}".replace(",", " "), "Charge du mois courant", ""),
        ("Dossiers lissés", f"{int(schedule_df['Lissé'].eq('Oui').sum()):,}".replace(",", " "), "Décalés sur les mois suivants", ""),
        ("Vigilance critique", f"{int(schedule_df['Régime de vigilance'].eq('Vigilance Critique').sum()):,}".replace(",", " "), "Régime critique", " is-alert"),
        ("Vigilance élevée", f"{int(schedule_df['Régime de vigilance'].eq('Vigilance Élevée').sum()):,}".replace(",", " "), "Régime élevé", ""),
        ("En retard théorique", f"{int((pd.to_datetime(schedule_df['Date prochaine revue théorique'], errors='coerce') < today).sum()):,}".replace(",", " "), "Échéance théorique dépassée", " is-alert"),
    ]
    st.markdown('<h3 class="cm-section-title">Bandeau de synthèse</h3>', unsafe_allow_html=True)
    st.markdown(
        "<div class='cm-kpi-band'>"
        + "".join(
            f"<div class='cm-kpi-card{extra_class}'><div class='cm-kpi-label'>{escape(label)}</div><div class='cm-kpi-value'>{escape(value)}</div><div class='cm-kpi-sub'>{escape(sub)}</div></div>"
            for label, value, sub, extra_class in cards
        )
        + "</div>",
        unsafe_allow_html=True,
    )



def build_review_export_dataframe(schedule_df: pd.DataFrame) -> pd.DataFrame:
    if schedule_df is None or schedule_df.empty:
        return pd.DataFrame(
            columns=[
                "SIREN",
                "Dénomination",
                "Régime de vigilance",
                "Fréquence (mois)",
                "Date de base",
                "Date théorique",
                "Date prochaine revue",
                "Lissé",
                "Décalage (mois)",
            ]
        )

    export_df = schedule_df[[
        "SIREN",
        "Dénomination",
        "Régime de vigilance",
        "Fréquence (mois)",
        "Date de base",
        "Date prochaine revue théorique",
        "Date prochaine revue",
        "Lissé",
        "Décalage (mois)",
    ]].copy()
    export_df = export_df.rename(
        columns={
            "Date prochaine revue théorique": "Date théorique",
            "Date prochaine revue": "Date prochaine revue",
        }
    )
    for col in ["Date de base", "Date théorique", "Date prochaine revue"]:
        export_df[col] = pd.to_datetime(export_df[col], errors="coerce").dt.strftime("%d/%m/%Y").fillna("")
    return export_df



def apply_review_schedule_to_active_base(schedule_df: pd.DataFrame, user: dict) -> int:
    if schedule_df is None or schedule_df.empty:
        return 0

    path = active_dataset_path() / DATA_FILES["base"]
    if not path.exists():
        raise FileNotFoundError("Le fichier 01_Donnees_base_source.csv est introuvable dans le jeu actif.")

    base_raw = read_csv_semicolon(path)
    validate_required_columns(base_raw, "base")
    base_raw[SOC_COL] = normalize_societe_id(base_raw[SOC_COL])
    base_raw["SIREN"] = normalize_siren(base_raw["SIREN"])
    if "Date prochaine revue" not in base_raw.columns:
        base_raw["Date prochaine revue"] = ""

    updates = schedule_df[[SOC_COL, "SIREN", "Date prochaine revue"]].copy()
    updates[SOC_COL] = normalize_societe_id(updates[SOC_COL])
    updates["SIREN"] = normalize_siren(updates["SIREN"])
    updates["Date prochaine revue"] = pd.to_datetime(updates["Date prochaine revue"], errors="coerce").dt.strftime("%d/%m/%Y")
    updates = updates.dropna(subset=KEY_COLUMNS).drop_duplicates(subset=KEY_COLUMNS, keep="last")
    updates = updates.rename(columns={"Date prochaine revue": "Date prochaine revue__calc"})

    merged = base_raw.merge(updates, on=KEY_COLUMNS, how="left")
    mask = merged["Date prochaine revue__calc"].fillna("").astype(str).str.strip().ne("")
    updated_count = int(mask.sum())
    merged.loc[mask, "Date prochaine revue"] = merged.loc[mask, "Date prochaine revue__calc"]
    merged = merged.drop(columns=["Date prochaine revue__calc"])
    merged.to_csv(path, sep=";", index=False, encoding="utf-8-sig")

    manifest = load_manifest() or {}
    manifest["last_review_schedule_apply_at_utc"] = datetime.now(timezone.utc).isoformat()
    manifest["last_review_schedule_apply_by"] = user.get("username")
    manifest["last_review_schedule_apply_by_name"] = user.get("display_name")
    save_manifest(manifest)
    return updated_count



def render_review_planning_content(
    df: pd.DataFrame,
    *,
    user: dict | None = None,
    show_export: bool = True,
    allow_apply: bool = False,
    notice_key: str | None = None,
    section_caption: str | None = None,
    persist_settings: bool = False,
) -> pd.DataFrame:
    if notice_key and st.session_state.get(notice_key):
        st.success(str(st.session_state.pop(notice_key)))

    if section_caption:
        st.caption(section_caption)

    freq_map, capacity_map, recalc = render_review_rule_editor(df)
    if recalc and persist_settings:
        persist_review_planning_settings(freq_map, capacity_map, user)
        st.success("Planning recalculé avec les paramètres saisis. Les paramètres sont mémorisés pour la suite.")
    elif recalc:
        st.success("Planning recalculé avec les paramètres saisis.")

    schedule_df = build_review_schedule(df, freq_map, capacity_map)
    if schedule_df.empty:
        st.info("Aucune revue à planifier sur le périmètre filtré.")
        return schedule_df

    st.divider()
    render_review_schedule_kpis(schedule_df)

    st.divider()
    st.markdown('<h3 class="cm-section-title">Jalons temporels de l’ensemble des revues</h3>', unsafe_allow_html=True)
    chart_df = build_review_schedule_chart_table(schedule_df)
    render_review_schedule_chart(chart_df)

    if show_export or (allow_apply and user and user.get("role") == "admin"):
        st.divider()
        st.markdown('<h3 class="cm-section-title">Table de planification</h3>', unsafe_allow_html=True)
        export_df = build_review_export_dataframe(schedule_df)

        if allow_apply and user and user.get("role") == "admin":
            info_col, export_col, apply_col = st.columns([4.5, 1.4, 2.1])
        else:
            info_col, export_col = st.columns([5.8, 1.4])
            apply_col = None

        with info_col:
            st.caption("Table exportable par SIREN avec régime de vigilance, fréquence appliquée, date théorique et date planifiée. La diffusion met à jour la colonne Date prochaine revue du fichier 01 pour le périmètre courant.")
        with export_col:
            st.download_button(
                label="Exporter (.csv)",
                data=dataframe_to_csv_bytes(export_df),
                file_name="planification_des_revues.csv",
                mime="text/csv",
                type="secondary",
                key="export_review_schedule_csv",
                use_container_width=True,
            )
        if apply_col is not None:
            with apply_col:
                if st.button(
                    "Diffuser dans l’onglet 01",
                    type="primary",
                    key="apply_review_schedule_to_base",
                    use_container_width=True,
                ):
                    updated_count = apply_review_schedule_to_active_base(schedule_df, user)
                    st.session_state[notice_key or "review_schedule_apply_notice"] = (
                        f"{updated_count} date(s) de prochaine revue ont été diffusées dans le fichier 01 sur le périmètre courant."
                    )
                    st.rerun()

        render_small_table(export_df, bold_numbers=False)

    return schedule_df



def render_review_planning_glossary_expander() -> None:
    glossary_rows = [
        ["Régime de vigilance", "Niveau de vigilance normalisé utilisé par l’écran de planification : Critique, Élevée, Modérée, Allégée ou Aucune."],
        ["Fréquence (mois)", "Nombre de mois entre deux revues théoriques pour un régime de vigilance donné."],
        ["Capacité max / mois", "Nombre maximal de dossiers que l’écran autorise à planifier sur un même mois pour un régime de vigilance donné."],
        ["Date de base", "Date servant de point de départ au calcul de la prochaine revue théorique."],
        ["Source date de base", "Origine de la date de base : Date dernière revue, Dernière mise à jour vigilance ou Date du jour si aucune date n’est disponible."],
        ["Date prochaine revue théorique", "Date obtenue en ajoutant la fréquence du régime à la date de base, avant tout lissage de capacité."],
        ["Date prochaine revue", "Date finalement planifiée après lissage mensuel et application de la capacité maximale du régime."],
        ["Mois théorique", "Mois de rattachement de la date théorique de prochaine revue."],
        ["Mois planifié", "Mois finalement retenu après lissage de la charge mensuelle."],
        ["Lissé", "Indique si un dossier a été décalé à un mois ultérieur parce que la capacité du mois théorique était déjà atteinte."],
        ["Décalage (mois)", "Nombre de mois de décalage entre le mois théorique et le mois planifié."],
        ["Statut planning", "Lecture opérationnelle de l’échéance planifiée : En retard, À 30 jours, 31-90 jours ou Au-delà de 90 jours."],
        ["Bandeau de synthèse", "Bloc de KPI résumant le volume planifié, la charge du mois courant, les dossiers lissés et les régimes les plus sensibles."],
        ["Table de planification", "Tableau exportable par SIREN avec le régime, la fréquence, la date de base, la date théorique, la date planifiée et le lissage."],
        ["Diffuser dans l’onglet 01", "Action d’écriture qui met à jour la colonne Date prochaine revue du fichier 01 sur le périmètre courant."],
    ]

    calc_rows = [
        [
            "Base de l’écran Planification",
            "Le portefeuille filtré est transformé en calendrier de revues : normalisation du régime de vigilance, choix d’une date de base, calcul d’une date théorique puis lissage mensuel selon la capacité paramétrée par régime.",
            "SIREN du périmètre courant",
            "Les réglages de fréquence et de capacité sont modifiables par régime et réutilisés dans tout l’écran.",
        ],
        [
            "Régime de vigilance",
            "Normalisation de la colonne ‘Vigilance’ : texte contenant critique → Vigilance Critique ; élevée → Vigilance Élevée ; modérée → Vigilance Modérée ; allégée → Vigilance Allégée ; aucune → Vigilance Aucune ; à défaut → Vigilance Aucune.",
            "Société",
            "Cette normalisation alimente à la fois la fréquence par défaut et la capacité mensuelle du régime.",
        ],
        [
            "Date de base",
            "Priorité de calcul : 1) Date dernière revue si renseignée ; sinon 2) Vigilance Date de mise à jour ; sinon 3) Date du jour.",
            "Société",
            "La source retenue est affichée dans la colonne ‘Source date de base’.",
        ],
        [
            "Date prochaine revue théorique",
            "Date de base + fréquence (en mois) du régime de vigilance, puis normalisation sur la journée correspondante du mois cible.",
            "Société",
            "Cette date est calculée avant tout lissage de charge.",
        ],
        [
            "Lissage mensuel",
            "Pour chaque régime, tri par date théorique puis placement dans le mois théorique si la capacité n’est pas atteinte ; sinon décalage mois par mois jusqu’au premier mois disponible.",
            "Régime × mois",
            "Le lissage ne mélange pas les capacités de régimes différents.",
        ],
        [
            "Capacité max / mois",
            "Valeur paramétrable par régime, avec plancher à 1. Si le nombre de dossiers du mois théorique dépasse cette capacité, les dossiers excédentaires sont décalés sur les mois suivants.",
            "Régime de vigilance",
            "La capacité par défaut dépend du régime mais peut être modifiée à l’écran puis persistée.",
        ],
        [
            "Lissé / Décalage (mois)",
            "Lissé = Oui si le mois planifié est différent du mois théorique ; Décalage (mois) = nb de mois entre mois théorique et mois planifié.",
            "Société",
            "Permet de visualiser l’impact du lissage sur la charge de travail.",
        ],
        [
            "Statut planning",
            "Calcul sur l’écart entre la date planifiée et la date du jour : < 0 jour = En retard ; ≤ 30 jours = À 30 jours ; ≤ 90 jours = 31-90 jours ; sinon = Au-delà de 90 jours.",
            "Société",
            "La date planifiée est utilisée et non la date théorique.",
        ],
        [
            "Jalons temporels de l’ensemble des revues",
            "Agrégation mensuelle des dates planifiées : groupby(Mois planifié, Régime de vigilance), puis affichage en barres empilées avec total mensuel.",
            "Périmètre filtré",
            "L’horizon affiché couvre au moins les 12 prochains mois et s’étend si des dates planifiées vont au-delà.",
        ],
        [
            "Bandeau de synthèse",
            "SIREN planifiés = nb de lignes du calendrier ; Revues ce mois = nb de dates planifiées dans le mois courant ; Dossiers lissés = count(Lissé == Oui) ; En retard théorique = count(Date théorique < date du jour).",
            "Périmètre filtré",
            "Les compteurs Vigilance critique et Vigilance élevée proviennent directement de la colonne Régime de vigilance du calendrier.",
        ],
        [
            "Table de planification / Export CSV",
            "Export du calendrier visible par SIREN avec les colonnes régime, fréquence, date de base, date théorique, date planifiée, lissage et décalage.",
            "Périmètre filtré",
            "Le CSV reflète exactement le périmètre courant après filtres et réglages de fréquence/capacité.",
        ],
        [
            "Diffuser dans l’onglet 01",
            "Écriture des dates planifiées dans la colonne ‘Date prochaine revue’ du fichier 01 pour les couples [Société, SIREN] du périmètre courant.",
            "Périmètre filtré",
            "Réservé à l’administrateur et appliqué uniquement sur la base active.",
        ],
    ]

    with st.expander("Glossaire & calculs de l’écran Planification des revues", expanded=False):
        st.caption("Aide documentaire de lecture. Ce bloc n’a aucun impact sur les calculs, les lissages ni les diffusions de l’écran.")

        glossary_tab, calculation_tab = st.tabs(["Glossaire", "Calculs"])

        with glossary_tab:
            st.dataframe(
                pd.DataFrame(glossary_rows, columns=["Terme", "Définition"]),
                use_container_width=True,
                hide_index=True,
                height=520,
            )

        with calculation_tab:
            render_reference_table(
                pd.DataFrame(calc_rows, columns=["Indicateur", "Calcul / règle", "Périmètre", "Note"]),
                column_min_widths=["250px", "760px", "210px", "500px"],
            )



def compute_latest_indicator_update_from_row(row: pd.Series) -> pd.Timestamp | pd.NaT:
    date_values: list[pd.Timestamp] = []
    for col in row.index:
        if "Date de mise à jour" in str(col):
            parsed = pd.to_datetime(row.get(col), errors="coerce", dayfirst=True)
            if pd.notna(parsed):
                date_values.append(parsed)
    if not date_values:
        return pd.NaT
    return max(date_values)



def build_latest_history_snapshot(history_df: pd.DataFrame) -> pd.DataFrame:
    if history_df is None or history_df.empty:
        return history_df.iloc[0:0].copy() if isinstance(history_df, pd.DataFrame) else pd.DataFrame()

    work = history_df.copy()
    work["_cm_latest_history_date"] = work.apply(compute_latest_indicator_update_from_row, axis=1)
    work["_cm_latest_history_date_sort"] = pd.to_datetime(work["_cm_latest_history_date"], errors="coerce")
    work = work.sort_values(KEY_COLUMNS + ["_cm_latest_history_date_sort"], ascending=[True, True, False], na_position="last")
    latest = work.drop_duplicates(subset=KEY_COLUMNS, keep="first").drop(columns=["_cm_latest_history_date_sort"])
    return latest.reset_index(drop=True)



def build_indicator_snapshot_rows(indicator_rows: pd.DataFrame, *, suffix: str) -> pd.DataFrame:
    base_columns = list(KEY_COLUMNS)
    if indicator_rows is None or indicator_rows.empty:
        empty = pd.DataFrame(columns=base_columns)
        empty[f"Vigilance_{suffix}"] = pd.Series(dtype="string")
        empty[f"Risque_{suffix}"] = pd.Series(dtype="string")
        empty[f"Date_snapshot_{suffix}"] = pd.Series(dtype="datetime64[ns]")
        empty["_cm_history_order"] = pd.Series(dtype="int64")
        for label in RISK_ORDER:
            empty[f"Nb_{normalize_text_for_matching(label).replace(' ', '_')}_{suffix}"] = pd.Series(dtype="int64")
        return empty

    records: list[dict[str, object]] = []
    for row_order, (_, row) in enumerate(indicator_rows.iterrows()):
        item: dict[str, object] = {
            SOC_COL: row.get(SOC_COL),
            "SIREN": row.get("SIREN"),
            f"Vigilance_{suffix}": canonical_vigilance_label(row.get("Vigilance statut")) or pd.NA,
            f"Risque_{suffix}": derive_indicator_row_risk(row) or pd.NA,
            f"Date_snapshot_{suffix}": compute_latest_indicator_update_from_row(row),
            "_cm_history_order": row_order,
        }
        counts = build_indicator_status_counts_from_row(row)
        for label in RISK_ORDER:
            safe_label = normalize_text_for_matching(label).replace(" ", "_")
            item[f"Nb_{safe_label}_{suffix}"] = int(counts.get(label, 0))
        records.append(item)

    snapshot = pd.DataFrame(records)
    if snapshot.empty:
        return snapshot
    for col in [f"Vigilance_{suffix}", f"Risque_{suffix}"]:
        snapshot[col] = snapshot[col].astype("string")
    snapshot[f"Date_snapshot_{suffix}"] = pd.to_datetime(snapshot[f"Date_snapshot_{suffix}"], errors="coerce")
    snapshot["_cm_history_order"] = pd.to_numeric(snapshot["_cm_history_order"], errors="coerce").fillna(0).astype(int)
    for label in RISK_ORDER:
        safe_label = normalize_text_for_matching(label).replace(" ", "_")
        col = f"Nb_{safe_label}_{suffix}"
        snapshot[col] = pd.to_numeric(snapshot[col], errors="coerce").fillna(0).astype(int)
    return snapshot.reset_index(drop=True)



def build_history_timeline_summary(history_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, pd.Series], dict[str, pd.Series]]:
    if history_df is None or history_df.empty:
        empty = pd.DataFrame(columns=[
            SOC_COL,
            "SIREN",
            "Nb snapshots historiques",
            "Première date historique",
            "Dernière date historique",
            "Vigilance_historique_depart",
            "Risque_historique_depart",
            "Vigilance_historique_dernier",
            "Risque_historique_dernier",
            "Changement_historique_vigilance",
            "Changement_historique_risque",
            "Historique_a_bouge",
        ])
        return empty, {}, {}

    raw_rows = history_df.reset_index(drop=True).copy()
    snapshot_rows = build_indicator_snapshot_rows(raw_rows, suffix="historique")
    if snapshot_rows.empty:
        return pd.DataFrame(), {}, {}

    first_rows_by_key: dict[str, pd.Series] = {}
    last_rows_by_key: dict[str, pd.Series] = {}
    summaries: list[dict[str, object]] = []
    for (soc, siren), group in snapshot_rows.groupby(KEY_COLUMNS, dropna=False, sort=False):
        ordered = group.copy()
        ordered["_cm_date_sort"] = pd.to_datetime(ordered["Date_snapshot_historique"], errors="coerce")
        ordered = ordered.sort_values(["_cm_date_sort", "_cm_history_order"], ascending=[True, True], na_position="last", kind="stable")
        if ordered.empty:
            continue
        first_row = ordered.iloc[0].copy()
        last_row = ordered.iloc[-1].copy()
        first_raw = raw_rows.iloc[int(first_row.get("_cm_history_order", 0) or 0)].copy()
        last_raw = raw_rows.iloc[int(last_row.get("_cm_history_order", 0) or 0)].copy()
        key = f"{soc}|{siren}"
        first_rows_by_key[key] = first_raw
        last_rows_by_key[key] = last_raw
        unique_vigilance = {str(v).strip() for v in ordered["Vigilance_historique"].dropna().astype(str) if str(v).strip()}
        unique_risk = {str(v).strip() for v in ordered["Risque_historique"].dropna().astype(str) if str(v).strip()}
        change_vig = len(unique_vigilance) > 1
        change_risk = len(unique_risk) > 1
        summaries.append({
            SOC_COL: soc,
            "SIREN": siren,
            "Nb snapshots historiques": int(len(ordered)),
            "Première date historique": pd.to_datetime(first_row.get("Date_snapshot_historique"), errors="coerce"),
            "Dernière date historique": pd.to_datetime(last_row.get("Date_snapshot_historique"), errors="coerce"),
            "Vigilance_historique_depart": first_row.get("Vigilance_historique"),
            "Risque_historique_depart": first_row.get("Risque_historique"),
            "Vigilance_historique_dernier": last_row.get("Vigilance_historique"),
            "Risque_historique_dernier": last_row.get("Risque_historique"),
            "Changement_historique_vigilance": bool(change_vig),
            "Changement_historique_risque": bool(change_risk),
            "Historique_a_bouge": bool(change_vig or change_risk),
        })
    summary = pd.DataFrame(summaries)
    if summary.empty:
        return summary, first_rows_by_key, last_rows_by_key
    for col in ["Vigilance_historique_depart", "Risque_historique_depart", "Vigilance_historique_dernier", "Risque_historique_dernier"]:
        summary[col] = summary[col].astype("string")
    for col in ["Première date historique", "Dernière date historique"]:
        summary[col] = pd.to_datetime(summary[col], errors="coerce")
    for col in ["Nb snapshots historiques"]:
        summary[col] = pd.to_numeric(summary[col], errors="coerce").fillna(0).astype(int)
    return summary.reset_index(drop=True), first_rows_by_key, last_rows_by_key



def build_indicator_status_counts_from_row(row: pd.Series) -> dict[str, int]:
    counts = {label: 0 for label in RISK_ORDER}
    for column_name in row.index:
        raw_name = str(column_name)
        if raw_name == "Vigilance statut" or not re.search(r"(?i)\bstatut\b", raw_name):
            continue
        status = canonical_risk_label(row.get(column_name))
        if status in counts:
            counts[status] += 1
    return counts



def derive_indicator_row_risk(row: pd.Series) -> str:
    counts = build_indicator_status_counts_from_row(row)
    for label in RISK_ORDER:
        if counts.get(label, 0) > 0:
            return label
    return ""



def build_indicator_snapshot_frame(indicator_rows: pd.DataFrame, *, suffix: str) -> pd.DataFrame:
    base_columns = list(KEY_COLUMNS)
    if indicator_rows is None or indicator_rows.empty:
        empty = pd.DataFrame(columns=base_columns)
        empty[f"Vigilance_{suffix}"] = pd.Series(dtype="string")
        empty[f"Risque_{suffix}"] = pd.Series(dtype="string")
        empty[f"Date_snapshot_{suffix}"] = pd.Series(dtype="datetime64[ns]")
        for label in RISK_ORDER:
            empty[f"Nb_{normalize_text_for_matching(label).replace(' ', '_')}_{suffix}"] = pd.Series(dtype="int64")
        return empty

    records: list[dict[str, object]] = []
    for _, row in indicator_rows.iterrows():
        item: dict[str, object] = {
            SOC_COL: row.get(SOC_COL),
            "SIREN": row.get("SIREN"),
            f"Vigilance_{suffix}": canonical_vigilance_label(row.get("Vigilance statut")) or pd.NA,
            f"Risque_{suffix}": derive_indicator_row_risk(row) or pd.NA,
            f"Date_snapshot_{suffix}": compute_latest_indicator_update_from_row(row),
        }
        counts = build_indicator_status_counts_from_row(row)
        for label in RISK_ORDER:
            safe_label = normalize_text_for_matching(label).replace(" ", "_")
            item[f"Nb_{safe_label}_{suffix}"] = int(counts.get(label, 0))
        records.append(item)

    snapshot = pd.DataFrame(records)
    if snapshot.empty:
        return snapshot
    for col in [f"Vigilance_{suffix}", f"Risque_{suffix}"]:
        snapshot[col] = snapshot[col].astype("string")
    snapshot[f"Date_snapshot_{suffix}"] = pd.to_datetime(snapshot[f"Date_snapshot_{suffix}"], errors="coerce")
    for label in RISK_ORDER:
        safe_label = normalize_text_for_matching(label).replace(" ", "_")
        col = f"Nb_{safe_label}_{suffix}"
        snapshot[col] = pd.to_numeric(snapshot[col], errors="coerce").fillna(0).astype(int)
    return snapshot.drop_duplicates(subset=KEY_COLUMNS, keep="first").reset_index(drop=True)



def compare_ranked_status(previous_status: object, current_status: object, rank_map: dict[str, int]) -> str:
    previous = "" if previous_status is None or pd.isna(previous_status) else str(previous_status).strip()
    current = "" if current_status is None or pd.isna(current_status) else str(current_status).strip()
    if not previous:
        return "Sans historique"
    if not current:
        return "Non renseigné"
    previous_rank = rank_map.get(previous)
    current_rank = rank_map.get(current)
    if previous_rank is None or current_rank is None:
        return "Non comparable"
    if current_rank < previous_rank:
        return "Se dégrade"
    if current_rank > previous_rank:
        return "S’améliore"
    return "Stable"



def compute_indicator_evolution_status(previous_status: object, current_status: object) -> str:
    previous = canonical_risk_label(previous_status)
    current = canonical_risk_label(current_status)
    if not previous and current:
        return "Nouveau"
    if previous and not current:
        return "Sorti"
    if not previous and not current:
        return "Non comparable"
    previous_rank = RISK_RANK.get(previous)
    current_rank = RISK_RANK.get(current)
    if previous_rank is None or current_rank is None:
        return "Non comparable"
    if current_rank < previous_rank:
        return "Se dégrade"
    if current_rank > previous_rank:
        return "S’améliore"
    return "Stable"



def indicator_status_payload_from_row(row: pd.Series) -> dict[str, dict[str, object]]:
    if row is None or (isinstance(row, float) and np.isnan(row)):
        return {}
    table = build_indicator_table_from_series(row)
    if table is None or table.empty:
        return {}
    mapping: dict[str, dict[str, object]] = {}
    for _, item in table.iterrows():
        indicator_name = str(item.get("Indicateur", "") or "").strip()
        if not indicator_name or indicator_name in CLASSIFICATION_EXCLUDED_INDICATORS:
            continue
        status = canonical_risk_label(item.get("Statut"))
        if not status:
            continue
        mapping[indicator_name] = {
            "Famille indicateur": classify_analysis_indicator_family(indicator_name),
            "Statut": status,
            "Valeur": item.get("Valeur"),
            "Date de mise à jour": pd.to_datetime(item.get("Date de mise à jour"), errors="coerce"),
            "Commentaire": item.get("Commentaire"),
        }
    return mapping



def build_client_indicator_deltas(current_row: pd.Series, history_row: pd.Series | None) -> pd.DataFrame:
    current_mapping = indicator_status_payload_from_row(current_row)
    history_mapping = indicator_status_payload_from_row(history_row) if history_row is not None else {}
    indicator_names = sorted(set(current_mapping.keys()) | set(history_mapping.keys()))
    rows: list[dict[str, object]] = []
    for indicator_name in indicator_names:
        current_item = current_mapping.get(indicator_name, {})
        history_item = history_mapping.get(indicator_name, {})
        history_status = history_item.get("Statut")
        current_status = current_item.get("Statut")
        evolution = compute_indicator_evolution_status(history_status, current_status)
        if evolution == "Non comparable":
            continue
        rows.append(
            {
                "Famille indicateur": current_item.get("Famille indicateur") or history_item.get("Famille indicateur") or classify_analysis_indicator_family(indicator_name),
                "Indicateur": indicator_name,
                "Statut historique": history_status or "Non renseigné",
                "Statut courant": current_status or "Non renseigné",
                "Évolution": evolution,
                "Valeur historique": history_item.get("Valeur"),
                "Valeur courante": current_item.get("Valeur"),
                "Date historique": history_item.get("Date de mise à jour"),
                "Date courante": current_item.get("Date de mise à jour"),
                "Commentaire courant": current_item.get("Commentaire"),
            }
        )
    deltas = pd.DataFrame(rows)
    if deltas.empty:
        return deltas
    return deltas.sort_values(["Famille indicateur", "Indicateur"], kind="stable").reset_index(drop=True)



def build_evolution_comparison_dataset(
    portfolio_df: pd.DataFrame,
    indicators_df: pd.DataFrame,
    history_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, pd.DataFrame], pd.DataFrame]:
    identity_columns = [
        SOC_COL,
        "SIREN",
        "Dénomination",
        "Segment",
        "Pays de résidence",
        "Produit(service) principal",
        "Canal d’opérations principal 12 mois",
        "Analyste",
        "Valideur",
        "Statut EDD",
        "Vigilance",
        "Risque",
        "Nb historique",
    ]
    identity_columns = [col for col in identity_columns if col in portfolio_df.columns]
    current_identity = build_unique_client_snapshot(portfolio_df, identity_columns)
    current_snapshot = build_indicator_snapshot_frame(indicators_df, suffix="courant")
    history_summary, first_history_rows_by_key, last_history_rows_by_key = build_history_timeline_summary(history_df)
    latest_history_rows = build_latest_history_snapshot(history_df)

    merged = current_identity.merge(current_snapshot, on=KEY_COLUMNS, how="left")
    merged = merged.merge(history_summary, on=KEY_COLUMNS, how="left")
    merged["Historique disponible"] = merged.get("Vigilance_historique_depart", pd.Series(index=merged.index, dtype="string")).notna()
    merged["Vigilance historique"] = merged.get("Vigilance_historique_depart").fillna("Sans historique")
    merged["Vigilance dernier historique"] = merged.get("Vigilance_historique_dernier").fillna("Sans historique")
    merged["Vigilance courante"] = merged.get("Vigilance_courant").fillna("Non renseigné")
    merged["Risque historique"] = merged.get("Risque_historique_depart").fillna("Sans historique")
    merged["Risque dernier historique"] = merged.get("Risque_historique_dernier").fillna("Sans historique")
    merged["Risque courant"] = merged.get("Risque_courant").fillna("Non renseigné")
    merged["Première date historique"] = pd.to_datetime(merged.get("Première date historique"), errors="coerce")
    merged["Dernière date historique"] = pd.to_datetime(merged.get("Dernière date historique"), errors="coerce")
    merged["Nb snapshots historiques"] = pd.to_numeric(merged.get("Nb snapshots historiques"), errors="coerce").fillna(0).astype(int)
    merged["Historique a bougé"] = merged.get("Historique_a_bouge", pd.Series(False, index=merged.index)).fillna(False).astype(bool)
    merged["Évolution vigilance"] = merged.apply(
        lambda row: compare_ranked_status(row.get("Vigilance_historique_depart"), row.get("Vigilance_courant"), VIGILANCE_RANK),
        axis=1,
    )
    merged["Évolution risque"] = merged.apply(
        lambda row: compare_ranked_status(row.get("Risque_historique_depart"), row.get("Risque_courant"), RISK_RANK),
        axis=1,
    )
    merged["Évolution historique vigilance"] = merged.apply(
        lambda row: compare_ranked_status(row.get("Vigilance_historique_depart"), row.get("Vigilance_historique_dernier"), VIGILANCE_RANK),
        axis=1,
    )
    merged["Évolution historique risque"] = merged.apply(
        lambda row: compare_ranked_status(row.get("Risque_historique_depart"), row.get("Risque_historique_dernier"), RISK_RANK),
        axis=1,
    )

    detail_map: dict[str, pd.DataFrame] = {}
    indicator_rows: list[dict[str, object]] = []
    current_rows_by_key = {
        f"{row.get(SOC_COL)}|{row.get('SIREN')}": row
        for _, row in indicators_df.iterrows()
    }

    overall_evolution: list[str] = []
    indicator_aggraves: list[int] = []
    indicator_ameliores: list[int] = []
    indicator_stables: list[int] = []
    indicator_nouveaux: list[int] = []
    indicator_sortis: list[int] = []
    bascules_majeures: list[bool] = []

    for _, merged_row in merged.iterrows():
        client_key = f"{merged_row.get(SOC_COL)}|{merged_row.get('SIREN')}"
        current_row = current_rows_by_key.get(client_key)
        history_row = first_history_rows_by_key.get(client_key)
        deltas = build_client_indicator_deltas(current_row, history_row) if current_row is not None else pd.DataFrame()
        detail_map[client_key] = deltas
        degraded = int(deltas["Évolution"].eq("Se dégrade").sum()) if not deltas.empty else 0
        improved = int(deltas["Évolution"].eq("S’améliore").sum()) if not deltas.empty else 0
        stable = int(deltas["Évolution"].eq("Stable").sum()) if not deltas.empty else 0
        new_items = int(deltas["Évolution"].eq("Nouveau").sum()) if not deltas.empty else 0
        removed = int(deltas["Évolution"].eq("Sorti").sum()) if not deltas.empty else 0
        indicator_aggraves.append(degraded)
        indicator_ameliores.append(improved)
        indicator_stables.append(stable)
        indicator_nouveaux.append(new_items)
        indicator_sortis.append(removed)

        for _, delta_row in deltas.iterrows():
            indicator_rows.append(
                {
                    "Famille indicateur": delta_row.get("Famille indicateur"),
                    "Indicateur": delta_row.get("Indicateur"),
                    "Évolution": delta_row.get("Évolution"),
                    "Statut historique": delta_row.get("Statut historique"),
                    "Statut courant": delta_row.get("Statut courant"),
                    SOC_COL: merged_row.get(SOC_COL),
                    "SIREN": merged_row.get("SIREN"),
                }
            )

        vig_change = str(merged_row.get("Évolution vigilance", "")).strip()
        risk_change = str(merged_row.get("Évolution risque", "")).strip()
        has_history = bool(merged_row.get("Historique disponible"))
        if not has_history:
            overall_evolution.append("Sans historique")
        elif "Se dégrade" in {vig_change, risk_change}:
            overall_evolution.append("Se dégrade")
        elif "S’améliore" in {vig_change, risk_change} and "Se dégrade" not in {vig_change, risk_change}:
            overall_evolution.append("S’améliore")
        elif bool(merged_row.get("Historique a bougé")):
            overall_evolution.append("A bougé dans l’historique")
        elif vig_change == "Stable" and risk_change == "Stable":
            overall_evolution.append("Stable")
        else:
            overall_evolution.append("Mixte")

        bascule = (
            (merged_row.get("Vigilance courante") in CRITICAL_VIGILANCE and merged_row.get("Vigilance historique") not in CRITICAL_VIGILANCE)
            or (merged_row.get("Risque courant") == "Risque avéré" and merged_row.get("Risque historique") != "Risque avéré")
            or (degraded >= 2)
        ) if has_history else False
        bascules_majeures.append(bool(bascule))

    merged["Nb indicateurs aggravés"] = indicator_aggraves
    merged["Nb indicateurs améliorés"] = indicator_ameliores
    merged["Nb indicateurs stables"] = indicator_stables
    merged["Nb indicateurs nouveaux"] = indicator_nouveaux
    merged["Nb indicateurs sortis"] = indicator_sortis
    merged["Évolution globale"] = overall_evolution
    merged["Bascule majeure"] = np.where(bascules_majeures, "Oui", "Non")

    indicator_changes = pd.DataFrame(indicator_rows)
    if indicator_changes.empty:
        indicator_agg = pd.DataFrame(columns=[
            "Famille indicateur",
            "Indicateur",
            "Nb se dégrade",
            "Nb s’améliore",
            "Nb stables",
            "Nb nouveaux",
            "Nb sortis",
            "Statut historique dominant",
            "Statut courant dominant",
            "Solde net",
        ])
    else:
        work = indicator_changes.copy()
        def dominant_status(series: pd.Series) -> str:
            cleaned = [str(v).strip() for v in series.dropna().tolist() if str(v).strip() and str(v).strip() != "Non renseigné"]
            if not cleaned:
                return "Non renseigné"
            counts = pd.Series(cleaned).value_counts()
            max_count = counts.max()
            candidates = [status for status, count in counts.items() if count == max_count]
            return sorted(candidates, key=lambda item: RISK_RANK.get(item, 999))[0]

        indicator_agg = (
            work.groupby(["Famille indicateur", "Indicateur"], dropna=False)
            .agg(
                **{
                    "Nb se dégrade": ("Évolution", lambda s: int(s.eq("Se dégrade").sum())),
                    "Nb s’améliore": ("Évolution", lambda s: int(s.eq("S’améliore").sum())),
                    "Nb stables": ("Évolution", lambda s: int(s.eq("Stable").sum())),
                    "Nb nouveaux": ("Évolution", lambda s: int(s.eq("Nouveau").sum())),
                    "Nb sortis": ("Évolution", lambda s: int(s.eq("Sorti").sum())),
                    "Statut historique dominant": ("Statut historique", dominant_status),
                    "Statut courant dominant": ("Statut courant", dominant_status),
                }
            )
            .reset_index()
        )
        indicator_agg["Solde net"] = indicator_agg["Nb se dégrade"] - indicator_agg["Nb s’améliore"]
        indicator_agg = indicator_agg.sort_values(["Solde net", "Nb se dégrade", "Indicateur"], ascending=[False, False, True], kind="stable").reset_index(drop=True)

    merged = merged.sort_values(
        ["Bascule majeure", "Historique a bougé", "Nb indicateurs aggravés", "Évolution globale", "Dénomination"],
        ascending=[False, False, False, True, True],
        kind="stable",
    ).reset_index(drop=True)
    return merged, indicator_agg, detail_map, latest_history_rows



def build_evolution_distribution_frame(df: pd.DataFrame, *, historical_col: str, current_col: str, order: list[str], status_type: str) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["Source", "Statut", "Nb", "Type"])
    comparable = df[df["Historique disponible"]].copy()
    if comparable.empty:
        return pd.DataFrame(columns=["Source", "Statut", "Nb", "Type"])
    rows: list[dict[str, object]] = []
    for source_label, column_name in [("Dernier historique", historical_col), ("Courant", current_col)]:
        counts = comparable[column_name].astype(str).value_counts()
        for status in order:
            rows.append({"Source": source_label, "Statut": status, "Nb": int(counts.get(status, 0)), "Type": status_type})
    return pd.DataFrame(rows)



def build_evolution_transition_matrix(df: pd.DataFrame, *, historical_col: str, current_col: str, order: list[str]) -> pd.DataFrame:
    comparable = df[df["Historique disponible"]].copy()
    if comparable.empty:
        return pd.DataFrame(index=order, columns=order).fillna(0).astype(int)
    hist = pd.Categorical(comparable[historical_col], categories=order, ordered=True)
    curr = pd.Categorical(comparable[current_col], categories=order, ordered=True)
    matrix = pd.crosstab(hist, curr, dropna=False)
    matrix = matrix.reindex(index=order, columns=order, fill_value=0)
    matrix.index.name = "Historique"
    return matrix



def build_evolution_distribution_chart(df: pd.DataFrame, *, title: str, order: list[str], status_type: str) -> alt.Chart:
    if df.empty:
        return alt.Chart(pd.DataFrame({"Source": [], "Statut": [], "Nb": []})).mark_bar()
    color_map = {status: status_palette(status, status_type)[0] for status in order}
    return (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("Statut:N", sort=order, title=None),
            y=alt.Y("Nb:Q", title="Nb clients"),
            color=alt.Color("Source:N", title=None, scale=alt.Scale(domain=["Dernier historique", "Courant"], range=["#94A3B8", PRIMARY_COLOR])),
            xOffset=alt.XOffset("Source:N"),
            tooltip=["Source", "Statut", "Nb"],
        )
        .properties(height=320, title=title)
    )



def filter_evolution_dataframe(df: pd.DataFrame, evolution_filter: str) -> pd.DataFrame:
    if df is None or df.empty or evolution_filter == "Tous":
        return df
    if evolution_filter == "Bascules majeures":
        return df[df["Bascule majeure"] == "Oui"].reset_index(drop=True)
    return df[df["Évolution globale"] == evolution_filter].reset_index(drop=True)



def render_evolution_glossary_expander() -> None:
    glossary_rows = [
        ["Premier historique", "État historique le plus ancien exploitable dans le fichier 03 pour un couple Société / SIREN. Il sert de point de départ de comparaison dans l’écran Évolution."],
        ["Courant", "État actuel issu du fichier 02 pour le couple Société / SIREN."],
        ["Évolution vigilance", "Comparaison entre la vigilance du premier historique exploitable et la vigilance courante : Se dégrade, S’améliore, Stable ou Sans historique."],
        ["Évolution risque", "Comparaison entre le risque agrégé issu des statuts indicateurs du premier historique exploitable et le risque agrégé issu des statuts indicateurs courants."],
        ["Évolution globale", "Lecture synthétique par société : Se dégrade si vigilance ou risque se dégrade ; S’améliore si au moins un axe s’améliore sans dégradation ; A bougé dans l’historique si le dossier a changé dans le fichier 03 mais sans écart net entre départ et courant ; Stable si rien n’a bougé ; Sans historique sinon."],
        ["Bascule majeure", "Oui si la société entre en vigilance critique / élevée, passe en risque avéré, ou cumule au moins deux indicateurs qui se dégradent entre le dernier historique et le courant."],
        ["Indicateurs aggravés", "Indicateurs dont le statut courant est plus sévère que le statut du dernier historique."],
        ["Indicateurs nouveaux", "Indicateurs présents au courant mais absents du dernier historique disponible."],
        ["Indicateurs sortis", "Indicateurs présents dans le dernier historique mais absents du courant."],
        ["Solde net indicateur", "Nb de dégradations moins nb d’améliorations pour un indicateur donné sur le portefeuille filtré."],
    ]
    calc_rows = [
        [
            "Socle de comparaison",
            "L’écran compare le premier état historique exploitable du fichier 03 au courant du fichier 02, société par société. Il ne reconstitue pas encore toute la timeline multi-snapshots, mais il signale lorsqu’un dossier a bougé à l’intérieur de l’historique.",
            "Société / SIREN",
            "V1 de l’écran Évolution : pilotage simple, robuste et lisible.",
        ],
        [
            "Vigilance historique et courante",
            "Vigilance courante = colonne ‘Vigilance statut’ du fichier 02 normalisée. Vigilance historique = même logique sur le premier état exploitable retenu dans le fichier 03 ; le dernier historique reste visible pour comprendre les mouvements intermédiaires.",
            "Société",
            "La comparaison s’effectue uniquement si un historique existe.",
        ],
        [
            "Risque historique et courant",
            "Le risque agrégé est dérivé des statuts indicateurs : priorité à Risque avéré, puis Risque potentiel, Risque mitigé, Risque levé, Non calculable et Aucun risque détecté.",
            "Société",
            "Cette lecture repose exclusivement sur les statuts indicateurs des fichiers 02 et 03.",
        ],
        [
            "Évolution vigilance / risque",
            "L’ordre métier sert de référence : plus le rang courant est sévère que l’historique, plus la société se dégrade ; à l’inverse elle s’améliore.",
            "Société",
            "Les clients sans historique restent visibles mais sont marqués ‘Sans historique’.",
        ],
        [
            "Bascule majeure",
            "Vaut Oui si la société entre en vigilance critique / élevée, passe en risque avéré, ou cumule au moins deux indicateurs aggravés entre historique et courant.",
            "Société",
            "Permet de détecter rapidement les dossiers à reprendre en priorité.",
        ],
        [
            "Top indicateurs qui bougent",
            "Agrégation des évolutions indicateur par indicateur : nb se dégrade, nb s’améliore, nb stables, nb nouveaux, nb sortis et solde net sur le portefeuille filtré.",
            "Portefeuille filtré",
            "Le détail société permet ensuite d’ouvrir la comparaison indicateur par indicateur.",
        ],
    ]

    with st.expander("Glossaire & calculs de l’écran Évolution", expanded=False):
        st.caption("Aide documentaire de lecture. Ce bloc n’a aucun impact sur les calculs ni sur les filtres de l’écran.")
        glossary_tab, calculation_tab = st.tabs(["Glossaire", "Calculs"])
        with glossary_tab:
            st.dataframe(
                pd.DataFrame(glossary_rows, columns=["Terme", "Définition"]),
                use_container_width=True,
                hide_index=True,
                height=420,
            )
        with calculation_tab:
            render_reference_table(
                pd.DataFrame(calc_rows, columns=["Indicateur", "Calcul / règle", "Périmètre", "Note"]),
                column_min_widths=["260px", "760px", "210px", "500px"],
            )



def render_evolution_screen(portfolio: pd.DataFrame, indicators: pd.DataFrame, history: pd.DataFrame) -> None:
    render_home_hero("Évolution")
    nav = render_primary_navigation("evolution")
    if nav == "portfolio":
        open_portfolio_view()
        st.rerun()
    if nav == "analysis":
        open_analysis_view()
        st.rerun()
    if nav == "review_dates":
        open_review_dates_view()
        st.rerun()
    if nav == "review_simulations":
        open_review_simulations_view()
        st.rerun()

    top_left, top_right = st.columns([5.4, 1.1])
    with top_left:
        st.markdown('<h3 class="cm-section-title">Évolution du portefeuille</h3>', unsafe_allow_html=True)
        st.caption("Comparaison V1 entre le premier historique disponible du fichier 03 et l’état courant du fichier 02, avec signalement des dossiers qui ont bougé à l’intérieur de l’historique.")
    with top_right:
        if st.button("Réinitialiser", type="secondary", key="evolution_reset"):
            for label in ANALYSIS_PORTFOLIO_FILTER_LABELS:
                st.session_state[f"evolution_filter_{label}"] = "Tous"
            st.session_state["evolution_global_filter"] = "Tous"
            st.session_state["evolution_detail_client"] = ""
            st.rerun()

    filter_labels = ANALYSIS_PORTFOLIO_FILTER_LABELS
    selections: dict[str, str] = {}
    filter_cols = st.columns(5)
    for idx, label in enumerate(filter_labels):
        column = FILTER_MAPPING[label]
        options = ["Tous"] + non_empty_sorted(portfolio[column].unique()) if column in portfolio.columns else ["Tous"]
        state_key = f"evolution_filter_{label}"
        if st.session_state.get(state_key) not in options:
            st.session_state[state_key] = "Tous"
        with filter_cols[idx % 5]:
            selections[label] = st.selectbox(label, options=options, key=state_key)
        if idx % 5 == 4 and idx < len(filter_labels) - 1:
            filter_cols = st.columns(5)

    extra_left, extra_right = st.columns([1.2, 4.0])
    with extra_left:
        evolution_filter = st.selectbox(
            "Lecture",
            options=["Tous", "Se dégrade", "S’améliore", "A bougé dans l’historique", "Stable", "Sans historique", "Bascules majeures"],
            key="evolution_global_filter",
        )
    with extra_right:
        st.caption("Le filtre ‘Lecture’ s’applique au tableau des sociétés et au détail dossier ; les graphes et matrices restent calculés sur le périmètre filtré avant ce focus, pour préserver la vision portefeuille.")

    filtered_portfolio = apply_filters(portfolio, selections)
    if filtered_portfolio.empty:
        st.warning("Aucun client ne correspond au périmètre société + filtres sélectionnés.")
        return

    allowed_keys = {f"{soc}|{siren}" for soc, siren in zip(filtered_portfolio[SOC_COL], filtered_portfolio["SIREN"])}
    if not indicators.empty:
        scoped_indicators = indicators.copy()
        scoped_indicators["_cm_client_key"] = scoped_indicators[SOC_COL].astype(str) + "|" + scoped_indicators["SIREN"].astype(str)
        scoped_indicators = scoped_indicators[scoped_indicators["_cm_client_key"].isin(allowed_keys)].drop(columns=["_cm_client_key"]).copy()
    else:
        scoped_indicators = indicators.copy()
    if not history.empty:
        scoped_history = history.copy()
        scoped_history["_cm_client_key"] = scoped_history[SOC_COL].astype(str) + "|" + scoped_history["SIREN"].astype(str)
        scoped_history = scoped_history[scoped_history["_cm_client_key"].isin(allowed_keys)].drop(columns=["_cm_client_key"]).copy()
    else:
        scoped_history = history.copy()

    evolution_df, indicator_agg, detail_map, _latest_history = build_evolution_comparison_dataset(filtered_portfolio, scoped_indicators, scoped_history)
    if evolution_df.empty:
        st.info("Impossible de construire l’écran Évolution sur le périmètre courant.")
        return

    comparable_df = evolution_df[evolution_df["Historique disponible"]].copy()
    total_clients = len(evolution_df)
    comparable_clients = len(comparable_df)
    degraded_clients = int(evolution_df["Évolution globale"].eq("Se dégrade").sum())
    improved_clients = int(evolution_df["Évolution globale"].eq("S’améliore").sum())
    current_critical = int(evolution_df["Vigilance courante"].isin(CRITICAL_VIGILANCE).sum())
    historical_critical = int(comparable_df["Vigilance historique"].isin(CRITICAL_VIGILANCE).sum())
    current_confirmed = int(evolution_df["Risque courant"].eq("Risque avéré").sum())
    historical_confirmed = int(comparable_df["Risque historique"].eq("Risque avéré").sum())
    major_switches = int(evolution_df["Bascule majeure"].eq("Oui").sum())

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Sociétés analysées", f"{total_clients:,}".replace(",", " "))
    coverage_ratio = (comparable_clients / total_clients) if total_clients else 0.0
    history_moved_clients = int(evolution_df["Historique a bougé"].fillna(False).astype(bool).sum())
    c2.metric("Avec historique", f"{comparable_clients:,}".replace(",", " "), delta=f"{coverage_ratio:.0%} couverts")
    c3.metric("En dégradation", f"{degraded_clients:,}".replace(",", " "))
    c4.metric("En amélioration", f"{improved_clients:,}".replace(",", " "))
    c5.metric("Δ Vigilance critique", f"{current_critical:,}".replace(",", " "), delta=f"{current_critical - historical_critical:+d}")
    c6.metric("Δ Risque avéré", f"{current_confirmed:,}".replace(",", " "), delta=f"{current_confirmed - historical_confirmed:+d}")
    st.caption(f"Bascules majeures détectées : {major_switches} dossier(s). Dossiers ayant bougé dans l’historique : {history_moved_clients}. Les clients sans historique restent visibles mais ne sont pas intégrés aux matrices de transition.")

    if comparable_clients == 0:
        st.warning("Le périmètre filtré ne contient pas encore d’historique exploitable dans le fichier 03. L’écran est prêt, mais il n’y a pas encore de comparaison possible.")
        render_evolution_glossary_expander()
        return

    st.divider()
    left_chart, right_chart = st.columns(2)
    with left_chart:
        vig_chart_df = build_evolution_distribution_frame(
            evolution_df,
            historical_col="Vigilance historique",
            current_col="Vigilance courante",
            order=VIGILANCE_ORDER,
            status_type="vigilance",
        )
        st.altair_chart(
            build_evolution_distribution_chart(vig_chart_df, title="Vigilance : premier historique vs courant", order=VIGILANCE_ORDER, status_type="vigilance"),
            use_container_width=True,
        )
    with right_chart:
        risk_chart_df = build_evolution_distribution_frame(
            evolution_df,
            historical_col="Risque historique",
            current_col="Risque courant",
            order=RISK_ORDER,
            status_type="risk",
        )
        st.altair_chart(
            build_evolution_distribution_chart(risk_chart_df, title="Risque : premier historique vs courant", order=RISK_ORDER, status_type="risk"),
            use_container_width=True,
        )

    st.divider()
    m1, m2 = st.columns(2)
    with m1:
        st.markdown('<div class="cm-subsection-title">Transitions de vigilance (premier historique → courant)</div>', unsafe_allow_html=True)
        vigilance_matrix = build_evolution_transition_matrix(
            evolution_df,
            historical_col="Vigilance historique",
            current_col="Vigilance courante",
            order=VIGILANCE_ORDER,
        ).reset_index()
        render_small_table(vigilance_matrix, bold_numbers=False, scroll_x=True)
    with m2:
        st.markdown('<div class="cm-subsection-title">Transitions de risque (premier historique → courant)</div>', unsafe_allow_html=True)
        risk_matrix = build_evolution_transition_matrix(
            evolution_df,
            historical_col="Risque historique",
            current_col="Risque courant",
            order=RISK_ORDER,
        ).reset_index()
        render_small_table(risk_matrix, bold_numbers=False, scroll_x=True)

    st.divider()
    st.markdown('<h3 class="cm-section-title">Sociétés qui bougent</h3>', unsafe_allow_html=True)
    company_table = evolution_df[[
        "SIREN",
        "Dénomination",
        "Première date historique",
        "Dernière date historique",
        "Nb snapshots historiques",
        "Vigilance historique",
        "Vigilance dernier historique",
        "Vigilance courante",
        "Évolution vigilance",
        "Risque historique",
        "Risque dernier historique",
        "Risque courant",
        "Évolution risque",
        "Historique a bougé",
        "Nb indicateurs aggravés",
        "Nb indicateurs améliorés",
        "Nb indicateurs stables",
        "Nb indicateurs nouveaux",
        "Nb indicateurs sortis",
        "Évolution globale",
        "Bascule majeure",
    ]].copy()
    company_table["Première date historique"] = pd.to_datetime(company_table["Première date historique"], errors="coerce").dt.strftime("%d/%m/%Y").fillna("Sans historique")
    company_table["Dernière date historique"] = pd.to_datetime(company_table["Dernière date historique"], errors="coerce").dt.strftime("%d/%m/%Y").fillna("Sans historique")
    company_table["Historique a bougé"] = np.where(company_table["Historique a bougé"].fillna(False).astype(bool), "Oui", "Non")
    company_table = filter_evolution_dataframe(company_table.join(evolution_df[[SOC_COL]]), evolution_filter).drop(columns=[SOC_COL], errors="ignore")
    st.dataframe(company_table, use_container_width=True, hide_index=True, height=420)
    if not company_table.empty:
        st.download_button(
            label="Exporter les sociétés (.csv)",
            data=dataframe_to_csv_bytes(company_table),
            file_name="evolution_portefeuille_societes.csv",
            mime="text/csv",
            type="secondary",
            key="evolution_export_companies",
        )

    st.divider()
    st.markdown('<h3 class="cm-section-title">Indicateurs qui bougent</h3>', unsafe_allow_html=True)
    indicator_table = indicator_agg.copy()
    if evolution_filter == "Se dégrade":
        indicator_table = indicator_table[indicator_table["Nb se dégrade"] > 0]
    elif evolution_filter == "S’améliore":
        indicator_table = indicator_table[indicator_table["Nb s’améliore"] > 0]
    elif evolution_filter == "Stable":
        indicator_table = indicator_table[indicator_table["Nb stables"] > 0]
    elif evolution_filter == "Bascules majeures":
        baseline_clients = set(evolution_df.loc[evolution_df["Bascule majeure"] == "Oui", [SOC_COL, "SIREN"]].apply(tuple, axis=1).tolist())
        if baseline_clients and not indicator_agg.empty:
            scoped_changes = pd.DataFrame([
                row for key, deltas in detail_map.items() for row in deltas.to_dict("records")
                if tuple(key.split("|", 1)) in baseline_clients
            ])
            if not scoped_changes.empty:
                indicator_table = (
                    scoped_changes.groupby(["Famille indicateur", "Indicateur"], dropna=False)
                    .agg(
                        **{
                            "Nb se dégrade": ("Évolution", lambda s: int(s.eq("Se dégrade").sum())),
                            "Nb s’améliore": ("Évolution", lambda s: int(s.eq("S’améliore").sum())),
                            "Nb stables": ("Évolution", lambda s: int(s.eq("Stable").sum())),
                            "Nb nouveaux": ("Évolution", lambda s: int(s.eq("Nouveau").sum())),
                            "Nb sortis": ("Évolution", lambda s: int(s.eq("Sorti").sum())),
                            "Statut historique dominant": ("Statut historique", lambda s: s.dropna().astype(str).iloc[0] if len(s.dropna()) else "Non renseigné"),
                            "Statut courant dominant": ("Statut courant", lambda s: s.dropna().astype(str).iloc[0] if len(s.dropna()) else "Non renseigné"),
                        }
                    )
                    .reset_index()
                )
                indicator_table["Solde net"] = indicator_table["Nb se dégrade"] - indicator_table["Nb s’améliore"]
                indicator_table = indicator_table.sort_values(["Solde net", "Nb se dégrade", "Indicateur"], ascending=[False, False, True], kind="stable")
    st.dataframe(indicator_table.head(30), use_container_width=True, hide_index=True, height=380)
    if not indicator_table.empty:
        st.download_button(
            label="Exporter les indicateurs (.csv)",
            data=dataframe_to_csv_bytes(indicator_table),
            file_name="evolution_portefeuille_indicateurs.csv",
            mime="text/csv",
            type="secondary",
            key="evolution_export_indicators",
        )

    st.divider()
    st.markdown('<h3 class="cm-section-title">Détail par société</h3>', unsafe_allow_html=True)
    detail_source = filter_evolution_dataframe(evolution_df, evolution_filter)
    if detail_source.empty:
        st.info("Aucun dossier ne correspond au filtre de lecture sélectionné.")
    else:
        options = {
            f"{row['SIREN']} · {row.get('Dénomination', 'Non renseigné')}": f"{row.get(SOC_COL)}|{row['SIREN']}"
            for _, row in detail_source.iterrows()
        }
        selected_label = st.selectbox(
            "Choisir une société",
            options=list(options.keys()),
            key="evolution_detail_client",
        )
        selected_key = options.get(selected_label)
        selected_row = detail_source[detail_source.apply(lambda row: f"{row.get(SOC_COL)}|{row['SIREN']}" == selected_key, axis=1)].iloc[0]
        info_left, info_right = st.columns([1.3, 1.0])
        with info_left:
            detail_cards = [
                ("SIREN", selected_row.get("SIREN"), None),
                ("Dénomination", selected_row.get("Dénomination"), None),
                ("Vigilance historique", selected_row.get("Vigilance historique"), None),
                ("Vigilance dernier historique", selected_row.get("Vigilance dernier historique"), None),
                ("Vigilance courante", selected_row.get("Vigilance courante"), None),
                ("Évolution vigilance", selected_row.get("Évolution vigilance"), None),
                ("Risque historique", selected_row.get("Risque historique"), None),
                ("Risque dernier historique", selected_row.get("Risque dernier historique"), None),
                ("Risque courant", selected_row.get("Risque courant"), None),
                ("Évolution risque", selected_row.get("Évolution risque"), None),
            ]
            render_info_cards(detail_cards)
        with info_right:
            synthesis = pd.DataFrame(
                [
                    ["Historique disponible", "Oui" if bool(selected_row.get("Historique disponible")) else "Non"],
                    ["Nb snapshots historiques", int(selected_row.get("Nb snapshots historiques", 0) or 0)],
                    ["Première date historique", display_value(selected_row.get("Première date historique"))],
                    ["Dernière date historique", display_value(selected_row.get("Dernière date historique"))],
                    ["Historique a bougé", "Oui" if bool(selected_row.get("Historique a bougé")) else "Non"],
                    ["Nb indicateurs aggravés", int(selected_row.get("Nb indicateurs aggravés", 0) or 0)],
                    ["Nb indicateurs améliorés", int(selected_row.get("Nb indicateurs améliorés", 0) or 0)],
                    ["Nb indicateurs nouveaux", int(selected_row.get("Nb indicateurs nouveaux", 0) or 0)],
                    ["Bascule majeure", selected_row.get("Bascule majeure")],
                ],
                columns=["Indicateur", "Valeur"],
            )
            render_small_table(synthesis, bold_numbers=False)

        detail_df = detail_map.get(selected_key, pd.DataFrame()).copy()
        if detail_df.empty:
            st.info("Aucun delta indicateur n’est disponible pour ce dossier sur le périmètre courant.")
        else:
            for date_col in ["Date historique", "Date courante"]:
                if date_col in detail_df.columns:
                    detail_df[date_col] = pd.to_datetime(detail_df[date_col], errors="coerce").dt.strftime("%d/%m/%Y").fillna("")
            st.dataframe(detail_df, use_container_width=True, hide_index=True, height=420)

    st.divider()
    render_evolution_glossary_expander()



def render_review_planning_screen(portfolio: pd.DataFrame, user: dict) -> None:
    render_home_hero("Planification des revues")
    nav = render_primary_navigation("review_dates")
    if nav == "portfolio":
        open_portfolio_view()
        st.rerun()
    if nav == "analysis":
        open_analysis_view()
        st.rerun()
    if nav == "review_simulations":
        open_review_simulations_view()
        st.rerun()
    if nav == "evolution":
        open_evolution_view()
        st.rerun()

    top_left, top_right = st.columns([5.3, 1.2])
    with top_left:
        st.markdown('<h3 class="cm-section-title">Planification des revues</h3>', unsafe_allow_html=True)
        st.caption("La date de prochaine revue est calculée à partir du régime de vigilance, puis lissée sur les mois suivants si la capacité mensuelle du régime est dépassée.")
    with top_right:
        if st.button("Réinitialiser", type="secondary", key="review_planning_reset"):
            reset_review_filters()
            default_freq = {label: int(REVIEW_FREQUENCY_DEFAULTS.get(label, 12)) for label in VIGILANCE_ORDER}
            default_cap = {label: int(REVIEW_CAPACITY_DEFAULTS.get(label, 10)) for label in VIGILANCE_ORDER}
            for label in VIGILANCE_ORDER:
                st.session_state[f"review_freq_{review_setting_slug(label)}"] = default_freq[label]
                st.session_state[f"review_cap_{review_setting_slug(label)}"] = default_cap[label]
            persist_review_planning_settings(default_freq, default_cap, user)
            st.rerun()

    filter_labels = ["Vigilance", "Risque", "EDD", "Segment", "Pays", "Produit", "Canal", "Analyste", "Valideur"]
    selections: dict[str, str] = {}
    filter_cols = st.columns(5)
    for idx, label in enumerate(filter_labels):
        column = FILTER_MAPPING[label]
        options = ["Tous"] + non_empty_sorted(portfolio[column].unique()) if column in portfolio.columns else ["Tous"]
        state_key = "review_filter_" + label
        if st.session_state.get(state_key) not in options:
            st.session_state[state_key] = "Tous"
        with filter_cols[idx % 5]:
            selections[label] = st.selectbox(label, options=options, key=state_key)
        if idx % 5 == 4 and idx < len(filter_labels) - 1:
            filter_cols = st.columns(5)

    filtered = apply_filters(portfolio, selections)
    if filtered.empty:
        st.warning("Aucun client ne correspond au périmètre société + filtres sélectionnés.")
        return

    st.divider()
    render_review_planning_content(
        filtered,
        user=user,
        show_export=True,
        allow_apply=True,
        notice_key="review_schedule_apply_notice",
        persist_settings=True,
    )

    st.divider()
    render_review_planning_glossary_expander()



def render_user_header(user: dict, selected_societies: list[str], total_societies: int) -> None:
    manifest = load_manifest()
    with st.sidebar:
        st.markdown("### Session")
        st.write("**Utilisateur :** {}".format(user["display_name"]))
        st.write("**Rôle :** {}".format(user["role"]))
        st.write("**Sociétés sélectionnées :** {} / {}".format(len(selected_societies), total_societies))
        if manifest:
            st.write(
                "**Jeu actif :** {}".format(
                    format_manifest_date(manifest.get("published_at_utc"))
                )
            )
        logout_button()


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, layout="wide")
    inject_brand_theme()

    user = get_current_user()
    render_sidebar_brand(user)
    if user is None:
        login_form()
        return

    render_admin_data_manager(user)
    sync_view_state_from_query_params()

    try:
        base, indicators, history, portfolio = load_app_datasets()
    except NoPublishedDatasetError as exc:
        st.info(str(exc))
        return
    except (FileNotFoundError, DataValidationError, ValueError) as exc:
        st.error(str(exc))
        return
    except Exception as exc:
        st.error("Erreur inattendue au chargement des données : {}".format(exc))
        return

    selected_societies, allowed_societies = render_scope_selector(portfolio, user)
    scoped = restrict_to_societies(portfolio, selected_societies)
    render_user_header(user, selected_societies, len(allowed_societies))

    current_view = st.session_state.get("cm_view", "portfolio")
    scoped_indicators = restrict_to_societies(indicators, selected_societies)
    scoped_history = restrict_to_societies(history, selected_societies)
    if current_view == "client":
        render_client_screen(scoped, scoped_indicators, scoped_history, selected_societies, allowed_societies)
        return

    if current_view == "analysis":
        render_analysis_screen(scoped, scoped_indicators)
        return

    if current_view == "review_dates":
        render_review_planning_screen(scoped, user)
        return

    if current_view == "review_simulations":
        render_review_simulations_screen(scoped, user)
        return

    if current_view == "evolution":
        render_evolution_screen(scoped, scoped_indicators, scoped_history)
        return

    render_home_hero("Portefeuille 360°")
    nav = render_primary_navigation("portfolio")
    if nav == "analysis":
        open_analysis_view()
        st.rerun()
    if nav == "review_dates":
        open_review_dates_view()
        st.rerun()
    if nav == "review_simulations":
        open_review_simulations_view()
        st.rerun()
    if nav == "evolution":
        open_evolution_view()
        st.rerun()

    render_client_launcher(scoped, key_prefix="header")

    filters = render_filters(scoped)
    filtered = apply_filters(scoped, filters)

    if filtered.empty:
        st.warning("Aucun client ne correspond au périmètre société + filtres sélectionnés.")
        return

    render_kpis(filtered)
    st.divider()
    st.markdown('<h3 class="cm-section-title">Répartition</h3>', unsafe_allow_html=True)

    col_left, col_mid, col_right = st.columns([1.15, 1.15, 1.0])
    with col_left:
        st.markdown('<div class="cm-subsection-title">Vigilance</div>', unsafe_allow_html=True)
        vigilance_df = build_distribution(filtered, "Vigilance", VIGILANCE_ORDER).rename(columns={"Libellé": "Vigilance"})
        render_small_table(format_percent_column(vigilance_df), color_columns={"Vigilance": "vigilance"})

    with col_mid:
        st.markdown('<div class="cm-subsection-title">Risques Maximum</div>', unsafe_allow_html=True)
        risk_df = build_distribution(filtered, "Risque", RISK_ORDER).rename(columns={"Libellé": "Statut"})
        render_small_table(format_percent_column(risk_df), color_columns={"Statut": "risk"})

    alert_df = build_alert_table(filtered)

    with col_right:
        st.markdown('<div class="cm-subsection-title">Gouvernance</div>', unsafe_allow_html=True)
        render_small_table(alert_df)

    st.divider()
    st.markdown('<h3 class="cm-section-title">Concentrations</h3>', unsafe_allow_html=True)

    concentration_header_left, concentration_header_right = st.columns([1.25, 2.75])
    with concentration_header_left:
        st.markdown('<div class="cm-subsection-title">Classement des 4 TOP</div>', unsafe_allow_html=True)
        st.caption("Un tri unique s’applique aux segments, pays, produits et canaux.")
    with concentration_header_right:
        concentration_sort = st.radio(
            "Tri des concentrations",
            options=CONCENTRATION_SORT_OPTIONS,
            horizontal=True,
            label_visibility="collapsed",
            key="portfolio_concentration_sort_mode",
        )

    if concentration_sort == "% clients":
        st.caption("Tri actif : poids du groupe dans le portefeuille filtré.")
    elif concentration_sort == "% vigilance":
        st.caption("Tri actif : lecture métier des vigilances, de la plus sensible à la plus favorable (Critique → Élevée → Modérée → Allégée → Aucune).")
    else:
        st.caption("Tri actif : lecture métier des risques, de la plus sensible à la plus favorable (Avéré → Potentiel → Non calculable → Mitigé → Levé → Aucun).")

    top_segments_df = build_concentration_top_table(filtered, "Segment", "Segment", sort_mode=concentration_sort)
    top_pays_df = build_concentration_top_table(filtered, "Pays de résidence", "Pays", sort_mode=concentration_sort)
    top_produits_df = build_concentration_top_table(filtered, "Produit(service) principal", "Produit", sort_mode=concentration_sort)
    top_canaux_df = build_concentration_top_table(filtered, "Canal d’opérations principal 12 mois", "Canal", sort_mode=concentration_sort)

    t1, t2, t3, t4 = st.columns(4)
    with t1:
        render_top_block("Top segments", top_segments_df, dialog_key="segments", sort_mode=concentration_sort)
    with t2:
        render_top_block("Top pays", top_pays_df, dialog_key="pays", sort_mode=concentration_sort)
    with t3:
        render_top_block("Top produits", top_produits_df, dialog_key="produits", sort_mode=concentration_sort)
    with t4:
        render_top_block("Top canaux", top_canaux_df, dialog_key="canaux", sort_mode=concentration_sort)


    st.divider()
    st.markdown(
        '<h3 class="cm-section-title" style="white-space: nowrap;">Dossiers prioritaires</h3>',
        unsafe_allow_html=True,
    )
    priority_df = build_priority_table(filtered, top_n=10)
    priority_reference_columns = list(priority_df.columns)
    shared_portfolio_column_widths = infer_portfolio_shared_column_widths(priority_reference_columns)
    render_clickable_styled_dataframe(
        style_dataframe(priority_df),
        priority_df,
        use_container_width=True,
        height=420,
        hide_index=True,
        key_prefix="priority_table",
        preserve_order=True,
        auto_size_columns=False,
        pinned_columns=["SIREN", "Dénomination"],
        table_width="content",
        column_width_overrides=shared_portfolio_column_widths,
    )

    filtered_display_df = build_portfolio_underlying_table(
        filtered,
        include_hidden_societe=True,
        strip_status_prefixes=True,
        display_columns_only=True,
        product_label="Produits",
    )
    filtered_display_df = filtered_display_df[
        [col for col in priority_reference_columns if col in filtered_display_df.columns]
    ].copy()

    filtered_export_df = build_portfolio_underlying_table(
        filtered,
        include_hidden_societe=False,
        strip_status_prefixes=False,
        display_columns_only=False,
        product_label="Produit",
    )

    top_risks_export_sheets = [
        ("Top segments", top_segments_df),
        ("Top pays", top_pays_df),
        ("Top produits", top_produits_df),
        ("Top canaux", top_canaux_df),
    ]
    repartition_export_sheets = [
        ("Répartition vigilance", vigilance_df),
        ("Répartition risques", risk_df),
        ("Répartition gouvernance", alert_df),
    ]
    committee_pack_sheets = [
        ("Vue filtrée", filtered_export_df),
        ("Dossiers prioritaires", priority_df),
        *top_risks_export_sheets,
        *repartition_export_sheets,
    ]

    committee_report_pdf_bytes = None
    committee_report_pdf_error = ""
    if REPORTLAB_AVAILABLE:
        try:
            committee_report_pdf_bytes = build_committee_risk_report_pdf_bytes(
                filtered=filtered,
                selected_societies=selected_societies,
                filters=filters,
                vigilance_df=vigilance_df,
                risk_df=risk_df,
                alert_df=alert_df,
                top_risks_export_sheets=top_risks_export_sheets,
                priority_df=priority_df,
                filtered_export_df=filtered_export_df,
            )
        except Exception as exc:
            committee_report_pdf_error = str(exc)
    else:
        committee_report_pdf_error = PDF_DEPENDENCY_ERROR_MESSAGE

    with st.expander("Préparer votre Comité des Risques", expanded=False):
        st.caption("Pack Excel unique avec plusieurs onglets : vue filtrée, dossiers prioritaires, tops et répartitions.")
        st.download_button(
            label="Pack Comité des Risques (.xlsx)",
            data=build_committee_pack_excel_bytes(
                selected_societies=selected_societies,
                filters=filters,
                sheets=committee_pack_sheets,
            ),
            file_name=committee_pack_download_name(selected_societies),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True,
        )

        st.caption("Synthèse PDF exécutive bâtie sur la vue filtrée, la répartition, les concentrations et les dossiers prioritaires.")
        if committee_report_pdf_bytes:
            st.download_button(
                label="Rapport Comité des Risques (.pdf)",
                data=committee_report_pdf_bytes,
                file_name=committee_report_download_name(selected_societies),
                mime="application/pdf",
                use_container_width=True,
            )
        elif committee_report_pdf_error:
            st.info(committee_report_pdf_error)

    with st.expander("Aperçu des données sous-jacentes filtrées"):
        render_clickable_styled_dataframe(
            style_dataframe(filtered_display_df),
            filtered_display_df,
            use_container_width=True,
            height=420,
            hide_index=True,
            key_prefix="filtered_table",
            preserve_order=True,
            auto_size_columns=False,
            pinned_columns=["SIREN", "Dénomination"],
            table_width="content",
            column_width_overrides=shared_portfolio_column_widths,
        )

    render_portfolio_glossary_expander()




if __name__ == "__main__":
    main()

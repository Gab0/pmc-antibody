#!/bin/python
from typing import List, Optional

import re
import os

import pandas as pd


from ..query.querystring import AntibodyInformation


def load_dataset(sheet_name: str):

    # FIXME: There are better ways o load this;
    dataset_path = os.path.join(
        os.path.dirname(__file__),
        "citeab_output.xlsx"
    )

    dataset = pd.read_excel(
        dataset_path,
        sheet_name=sheet_name,
        skiprows=4
    )

    return dataset


def extract_all_ids(df: pd.DataFrame) -> List[str]:
    """ """
    def extract_link(link: str) -> List[str]:
        return re.findall(r"PMC[0-9]+", link)

    ids = []
    for link in df["URL"]:
        if isinstance(link, str):
            ids += extract_link(link)

    return ids


def is_url_pmc(url: str) -> bool:
    if not isinstance(url, str):
        return False

    if "europepmc.org" in url:
        return True

    return False


def benchmark_antibodies():
    invitrogen = ["Invitrogen", "eBioscience"]

    # NOTE: This list matches the antibody order found in the .xlsx reference table;
    return [
        # 01;
        AntibodyInformation("550280", "RM4-5", ["BD Biosciences", "BD Pharmingen", "BD"], "CD4"),
        AntibodyInformation("11-0041-82", "GK1.5", invitrogen, "CD4"),
        AntibodyInformation("ab183685", "EPR19514", "Abcam", "CD4"),
        AntibodyInformation("100401", "GK1.5", "BioLegend", "CD4"),
        AntibodyInformation("ab133616", "EPR6855", "Abcam", "CD4"),
        AntibodyInformation("AF1828", None, "R&D Systems", "TREM2"),
        AntibodyInformation("BAF1828", None, "R&D Systems", "TREM2"),

        # 08;
        AntibodyInformation("MA5-12542", "5C5.F8.C7", invitrogen, "ACTA1"),
        AntibodyInformation("AB5054", None, "MilliporeSigma", "CALB2"),
        AntibodyInformation("130-095-822", "ACSA-1", "Miltenyi Biotec", "GLAST"),  # Target??
        AntibodyInformation("60161.2", "2.4G2", "STEMCELL Technologies", "Fcgr3"),
        AntibodyInformation("9102", None, "Cell Signaling Technology", "MAPK"),  # Target alternative names??
        AntibodyInformation("3661", None, "Cell Signaling Technology", "ACACA"),
        AntibodyInformation("BA-2001", None, "Vector Laboratories", "Anti-Mouse"),
        AntibodyInformation("3533", None, "BioVision", "Collagenase 3 (Rat)"),  # Target gene name: MMP13??
        AntibodyInformation("BS10043", None, "Bioworld", "Anti-Rat"),  # Secondary antibody??
        AntibodyInformation("OABB00472", None, "Aviva Systems Biology", "CD68"),
        AntibodyInformation("PA1080", None, "Boster Biological Technology", "VEGFA"),
        AntibodyInformation("BE0146", "RMP1-14", "Bio X Cell", "PDCD1"),

        # 16;
        AntibodyInformation("A5862", None, "ABclonal", "XRCC5"),
        AntibodyInformation("AF933", None, "R&D Systems", "ACE2"),
        AntibodyInformation("ALX-801-002-C100", "C219", "Enzo Life Sciences", "ABCB1"),
        AntibodyInformation("NB100-165", None, "Novus Biologicals", "XRCC3"),
        AntibodyInformation("9285", None, "Cell Signaling Technology", "TP53"),
        AntibodyInformation("127-165-160", None, "Jackson ImmunoResearch", "Anti-Armenian Hamster"),  # Secondary antibody??

    ]

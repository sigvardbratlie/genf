import os
from pathlib import Path
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
import asyncio
from telethon import TelegramClient, events, sync
import nest_asyncio
import pandas as pd
from sibr_module import BigQuery, Logger
from typing import Literal
import difflib
import re



class GENF:
    def __init__(self,logger: Logger = None,bigquery_module : BigQuery = None):
        self._main_mappe = Path('/Users/sigvardbratlie/Library/CloudStorage/GoogleDrive-sigvard.bratlie@gmail.com/Min disk/GEN-F/')
        self._klinketil_mappe = self._main_mappe / '00_Rawfil_klinketil'
        self._python_mappe = self._main_mappe / 'Python'
        self._grunnfiler = self._python_mappe / 'Grunnfiler'
        self._fordelingsmappe = self._python_mappe / 'Fordeling'
        self._pameldingsmappe = self._python_mappe / 'Påmelding'
        self._okomomi_mappe = self._main_mappe / '02 - Økonomi'
        self._arbeidsavtale_mappe = self._main_mappe / 'Arbeidsavtale'
        if not logger:
            logger = Logger('GENF')
        self.logger = logger
        if not bigquery_module:
            bigquery_module = BigQuery(logger = self.logger, project_id="genf-446213")
        self.bq = bigquery_module


    def members(self) -> pd.DataFrame:
        """
        Leser inn medlemslisten fra Big Query DB og returnerer en dataframe
        :return:
        """
        return self.bq.read_bq('SELECT * FROM `genf-446213.genf.members`',read_type='pandas_gbq')
    def raw_telegram(self) -> pd.DataFrame:
        """
        Leser inn rådata fra telegram i Big Query DB og returnerer en dataframe
        :return:
        """
        return self.bq.read_bq('SELECT * FROM `genf-446213.genf.raw_telegram`', read_type='pandas_gbq')
    def members_id(self):
        """
        Leser inn medlemsliste med telegrambrukerID fra Big Query DB og returnerer en dataframe.
        Merk at Telegramgruppen inneholder 137 medlemmer,
        hvorav 4 ikke er medlemmer (Kristian Smith, Fredrik Bekkevold, Tom Larsen og Carine Stene).
        :return:
        """
        return self.bq.read_bq('SELECT * FROM `genf-446213.genf.members_id`', read_type='pandas_gbq')


    @staticmethod
    def set_options():
        pd.set_option('display.max_columns', None)
        pd.set_option('display.expand_frame_repr', False)

    def get_users(self, which_group: Literal["genf","mentor","hjelpementor"] = 'genf'):
        """
        Henter brukere fra telegram og lagrer i en Big Query DB "raw_telegram".
        Tlfnr og passord må oppgis. Tlf nr må oppggis i formatet 47 xxx xx xxx! (Uten +)
        :return: Returnerer raw_telegram dataframe
        """

        # These example values won't work. You must get your own api_id and
        # api_hash from https://my.telegram.org, under API Development.
        api_id = 21071304
        api_hash = '661abda0ed84f8c73ab2cbdadf38cb92'
        bot_token = '7405835573:AAFaCaf0-QbJ1KmHArEg8AqsvkZ-O1eNtqk'
        if which_group == 'genf':
            group_id = 'https://t.me/+fIonb9IjklliNmE0'
        elif which_group == 'mentor':
            group_id = "https://t.me/+tGvq1cvJpoE0MzI0"
        elif which_group == "hjelpementor":
            group_id = "https://t.me/+-a7v-IPwzPZjMDk8"

        async def get_users_async(client):  # Renamed to avoid confusion with the method name
            users_data = []
            await client.start()
            async for user in client.iter_participants(group_id):
                if not user.deleted:  # Check if the account still exists
                    users_data.append({
                        "UserID": user.id,
                        "Username": user.username,
                        "FirstName": user.first_name,
                        "LastName": user.last_name
                    })
            return users_data

        async def main():
            # Using 'async with' is safer for managing the client connection
            async with TelegramClient('session_name', api_id, api_hash) as client:
                users = await get_users_async(client)
                df = pd.DataFrame(users)
                # self.to_bq(df, 'raw_telegram', 'genf', if_exists='replace')
                # print("DB is replaced/created.")
                return df

        # Running the async main function
        nest_asyncio.apply()
        loop = asyncio.get_event_loop()
        # Fang resultatet og returner det
        df_users = loop.run_until_complete(main())
        return df_users



    def fix_timelister(self,filnavn:str):
        '''
        Leser inn timelister fra Klinketil.no og fordeler timer på ulike prosjekter.
        :param filnavn: Filen må være excel og må ha .xlsx som filendelse
        :return:
        '''
        filsti = self._main_mappe / (f'00_Rawfil_klinketil/{filnavn}')
        df = pd.read_excel(filsti)
        gruppe = 'Gruppe'
        prosjekt = 'Prosjekt'
        timer = 'Timer'
        feature = 'Navn'
        kontonr = 'Kontonr'
        alder = 'Alder'
        df[alder] = df[alder].astype(int, errors='ignore')
        if df[alder].isnull().sum() > 0:
            print(f'Antall manglende alder: {df[alder].isnull().sum()}')
            print(df[df[alder].isnull()])
            raise ValueError('Mangler alder for noen brukere')
        df_of = df[df[gruppe] == 'BCC OF']
        df_bd = df[(df[prosjekt] == 'Kiosk') & (df[alder] >= 18)]
        df_kiosk = df[(df[prosjekt] == 'Kiosk') & (df[alder] < 18)]
        df_buk = df[df[gruppe] == 'BUK']
        df_hvit = df[df[prosjekt] == 'Jobb hvit']
        df_glenne = df[df[gruppe] == 'Glenne Gård']
        df_fakturering = df[(df[prosjekt] == 'Vedkjøring Besteved') |(df[prosjekt] == 'Flyers Utedesign')]
        self.logger.info(f'Sum timer i OF før gruppering: {df_of[timer].sum()}')
        self.logger.info(f'Sum timer i BD før gruppering: {df_bd[timer].sum()}')
        self.logger.info(f'Sum timer i Gjers før gruppering: {df_kiosk[timer].sum()}')
        self.logger.info(f'Sum timer i BUK før gruppering: {df_buk[timer].sum()}')
        self.logger.info(f'Sum timer i Jobb hvit før gruppering: {df_hvit[timer].sum()}')
        self.logger.info(f'Sum timer i Glenne før gruppering: {df_glenne[timer].sum()}')
        self.logger.info(f'Sum timer i Fakturering før gruppering: {df_fakturering[timer].sum()}')
        self.logger.info('\n')

        # Summer timer per person
        df_of = df_of[[feature, timer]].groupby([feature]).sum().reset_index()
        #df_bd = df_bd[[feature, timer]].groupby([feature]).sum().reset_index()
        df_kiosk = df_kiosk[[feature, timer]].groupby([feature]).sum().reset_index()
        df_buk = df_buk[[feature, timer]].groupby([feature]).sum().reset_index()
        df_hvit = df_hvit[[feature, timer]].groupby([feature]).sum().reset_index()
        # df_glenne = df_glenne[[feature, timer]].groupby([feature]).sum().reset_index()
        df_fakturering = df_fakturering[[feature, timer]].groupby([feature]).sum().reset_index()
        # print(f'Sum timer i OF etter gruppering: {df_of[timer].sum()}')
        # print(f'Sum timer i BD etter gruppering: {df_bd[timer].sum()}')
        # print(f'Sum timer i Gjers etter gruppering: {df_g[timer].sum()}')
        # print(f'Sum timer i BUK etter gruppering: {df_buk[timer].sum()}')
        # print(f'Sum timer i Jobb hvit etter gruppering: {df_hvit[timer].sum()}')
        # print(f'Sum timer i Glenne etter gruppering: {df_glenne[timer].sum()}')
        # print(f'Sum timer i Besteved etter gruppering: {df_besteved[timer].sum()}')
        # print('\n')

        # Fjern eventuelle duplikater basert på 'user' før merge
        df_unique = df[[feature, kontonr, 'E-post', alder]].drop_duplicates(subset=feature)

        # Gjør mergen med unike verdier for hver bruker
        df_of = df_of.merge(df_unique, on=feature, how='left')
        #df_bd = df_bd.merge(df_unique, on=feature, how='left')
        df_kiosk = df_kiosk.merge(df_unique, on=feature, how='left')
        df_buk = df_buk.merge(df_unique, on=feature, how='left')
        df_hvit = df_hvit.merge(df_unique, on=feature, how='left')
        df_glenne = df_glenne.merge(df_unique, on=feature, how='left')
        df_fakturering = df_fakturering.merge(df_unique, on=feature, how='left')
        # print(f'Sum timer i OF etter merge: {df_of[timer].sum()}')
        # print(f'Sum timer i BD etter merge: {df_bd[timer].sum()}')
        # print(f'Sum timer i Gjers etter merge: {df_g[timer].sum()}')
        # print(f'Sum timer i BUK etter merge: {df_buk[timer].sum()}')
        # print(f'Sum timer i Jobb hvit etter merge: {df_hvit[timer].sum()}')
        # print(f'Sum timer i Glenne etter merge: {df_glenne[timer].sum()}')
        # print(f'Sum timer i Besteved etter merge: {df_besteved[timer].sum()}')
        # print('\n')


        mnd = (datetime.now() - relativedelta(months=1)).strftime('%m')
        aar = datetime.now().year
        sum_raw = round(df[timer].sum(),1)
        sum_of = round(df_of[timer].sum(),1)
        sum_bd = round(df_bd[timer].sum(),1)
        sum_kiosk = round(df_kiosk[timer].sum(),1)
        sum_buk = round(df_buk[timer].sum(),1)
        sum_hvit = round(df_hvit[timer].sum(),1)
        sum_glenne = round(df_glenne[timer].sum(),1)
        sum_fakturering = round(df_fakturering[timer].sum(),1)
        sum_all = sum_of + sum_bd + sum_kiosk + sum_buk + sum_hvit + sum_glenne + sum_fakturering
        self.logger.info(f'Sum timer fra Klinketil.no: {sum_raw}')
        self.logger.info(f'Sum etter fordeling: {sum_all}')
        if np.isclose(sum_raw, sum_all, rtol=1e-3):
            self.logger.info('Sum stemmer!')
            # Lagre til Excel med forskjellige faner
            filti_excel = f'{self._okomomi_mappe}/{aar}_{mnd}_timer_genf.xlsx'
            with pd.ExcelWriter(filti_excel,engine='xlsxwriter') as writer:
                df_of.to_excel(writer, sheet_name='bcc_of', index=False)
                df_bd.to_excel(writer, sheet_name='bd_kiosk', index=False)
                df_kiosk.to_excel(writer, sheet_name='kiosk_u16', index=False)
                df_buk.to_excel(writer, sheet_name='buk', index=False)
                df_hvit.to_excel(writer, sheet_name='jobb_hvit', index=False)
                df_glenne.to_excel(writer, sheet_name='glenne_gård', index=False)
                df_fakturering.to_excel(writer, sheet_name='fakturering_gjersjøen', index=False)
            df_bd.to_excel(f'{self._okomomi_mappe}/{aar}_{mnd}_timer_genf_BD.xlsx')
            self.logger.info('Excel-filnavn lagret!')
        else:
            self.logger.info('Sum stemmer ikke! Noen timer mangler. Excelfilnavn ikke lagret!')
            self.logger.info(f'Total mangler {sum_raw - sum_all} timer \n')
            self.logger.info(f'Sum BCC OF: {sum_of}')
            self.logger.info(f'Sum kiosk 16+ (BD): {sum_bd}')
            self.logger.info(f'Sum Kiosk U16: {sum_kiosk}')
            self.logger.info(f'Sum BUK: {sum_buk}')
            self.logger.info(f'Sum Jobb hvit: {sum_hvit}')
            self.logger.info(f'Sum Glenne Gård: {sum_glenne}')
            self.logger.info(f'Sum Fakturering: {sum_fakturering}')
            self.logger.info('\n')
            self.logger.info(f'Kiosk: {(sum_bd + sum_kiosk)}')
            self.logger.info(f'Kiosk KS direkte: {round(df[df[prosjekt] == "Kiosk"][timer].sum(),1)}')
    def get_påmeldte(self, filnavn: str, answer: str) -> pd.DataFrame:
        """
        Funksjonen tar inn påmeldingsfilen fra telegrampoll og returnerer hvem som har svart ja sortert på alder, kjønn og rolle.
        Funksjonen lagrer resultatet til en ny excel-fil.
        :param filnavn: navn på filen som skal sjekkes. NB: filnavn uten .csv
        :param answer: svar som skal sjekkes. For eksempel "Jeg kommer". Hentes fra pollen.
        :return:
        """

        medlemmer = pd.read_sql('members_id',con=self.engine)
        påmelding_sti = self._pameldingsmappe / (f'{filnavn}.csv')
        påmelding = pd.read_csv(påmelding_sti)
        # print(påmelding.head())
        påmelding.rename(columns={'id': 'UserID'}, inplace=True)
        påmelding['answer'] = påmelding['answer'].apply(lambda x: x.strip())
        answer = answer.strip()
        df = påmelding[påmelding['answer'] == answer]
        print(df.head())
        print(df.columns)
        print(f'Antall som kommer fra poll: {len(df)}')
        df = pd.merge(df[['UserID', 'timestamp']], medlemmer, on='UserID', how='inner')
        df_grouped = df.groupby(['Rolle', 'Kjønn']).apply(lambda x: x.sort_values('Fødselsår')).reset_index(drop=True)
        df_grouped['Full navn'] = df_grouped['Full navn'].apply(
            lambda x: ' '.join([i.capitalize() for i in x.split()]) if isinstance(x, str) else x)
        print(df_grouped.head())
        df_grouped.to_excel(os.path.join(self._fordelingsmappe, f'fordeling_genf_{filnavn}.xlsx'), index=False,engine='openpyxl')

        #Check if all members are in the list
        filsti_raw = self._pameldingsmappe / (filnavn + '.csv')
        raw = pd.read_csv(filsti_raw)
        raw['answer'] = raw['answer'].apply(lambda x: x.strip())
        raw = raw[raw['answer'] == answer.strip()]

        if len(df) == len(raw):
            print(f'Antall stemmer stemmer! Raw har {len(raw)} og påmeldt har {len(df)}')
        else:
            print(f'Antall stemmer stemmer ikke! Raw har {len(raw)} mens påmeldt har {len(df)}')
            not_in = raw[~raw['id'].isin(df['UserID'])]
            print(not_in)
        return df

    def get_all_timer(self,sesong = '25_26'):
        path = Path(
            f'/Users/sigvardbratlie/Library/CloudStorage/GoogleDrive-sigvard.bratlie@gmail.com/Min disk/GEN-F/00_Rawfil_klinketil/sesong_{sesong}')
        all_dfs = []
        for file in path.rglob('*.xlsx'):
            df_tmp = pd.read_excel(file, engine='openpyxl')
            all_dfs.append(df_tmp)

        df_ = pd.concat(all_dfs, ignore_index=True)
        df = df_
        new_cols = [col.lower().replace(".", "_").replace(" ", "_") for col in df.columns]
        df.columns = new_cols
        df["f_dato"] = pd.to_datetime(df["f_dato"], errors='coerce', dayfirst=False)
        df["dato"] = pd.to_datetime(df["dato"], errors='coerce', dayfirst=False)
        df["rolle"] = df["f_dato"].apply(lambda x: "genf" if x.year in [2012, 2011, 2010] else "hjelpementor" if x.year in [2009,2008] else "mentor")
        return df

    def normalize_name(self, name):
        """
        Normaliser navn: Gjør om til små bokstaver, fjern tegnsetting og ekstra mellomrom.
        """
        if pd.isna(name):
            return ''
        name = str(name).lower()
        name = re.sub(r'[^\w\s]', '', name)  # Fjern tegnsetting
        name = ' '.join(name.split())  # Fjern ekstra mellomrom
        return name

    def get_first_name(self, full_name):
        """
        Hent fornavn fra fullnavn.
        """
        if pd.isna(full_name):
            return ''
        parts = str(full_name).split()
        return parts[0] if parts else ''

    def match_dataframes(self,
                         df_telegram,
                         df_members,
                         name_dict_tg:  dict = None ,
                         name_dict_mem : dict = None,
                         userid_col='UserID', similarity_threshold=0.85):
        """
        Matcher to dataframes basert på navn med fallback-logikk.

        - df_telegram: Dataframe med Telegram-brukere (inneholder fullnavn, fornavn, USERID).
        - df_members: Dataframe med medlemsliste (inneholder korrekte fullnavn).
        - full_name_col_tg: Kolonnenavn for fullnavn i df_telegram.
        - first_name_col_tg: Kolonnenavn for fornavn i df_telegram (hvis separat).
        - full_name_col_mem: Kolonnenavn for fullnavn i df_members.
        - userid_col: Kolonnenavn for USERID i df_telegram.
        - similarity_threshold: Minimum similarity score for match (0-1).

        Returnerer df_members med en ny kolonne 'Matched_USERID' og 'Match_Type' ('Full' eller 'First').

        Bruker difflib for å håndtere partial matches og variasjoner (f.eks. mellomnavn).
        """

        if name_dict_tg is None:
            name_dict_tg = {"first_name": "FirstName", "last_name": "LastName", "full_name": "FullName"}
        if name_dict_mem is None:
            name_dict_mem = {"first_name": "FirstName", "last_name": "LastName", "full_name": "FullName"}

        full_name_col_tg = name_dict_tg.get("full_name")
        first_name_col_tg = name_dict_tg.get("first_name")
        full_name_col_mem = name_dict_mem.get("full_name")


        if name_dict_tg.get("full_name") not in df_telegram.columns:
            df_telegram[name_dict_tg.get("full_name")] = df_telegram[name_dict_tg.get("first_name")] + " " + df_telegram[name_dict_tg.get("last_name")]
        if name_dict_mem.get("full_name") not in df_members.columns:
            df_members[name_dict_mem.get("full_name")] = df_members[name_dict_mem.get("first_name")] + " " + df_members[name_dict_mem.get("last_name")]

        df_result = df_members.copy()
        df_result['Matched_USERID'] = None
        df_result['Match_Type'] = None

        # Normaliser navn i begge dataframes
        df_telegram['norm_full'] = df_telegram[full_name_col_tg].apply(self.normalize_name)
        if first_name_col_tg not in df_telegram.columns:
            df_telegram['norm_first'] = df_telegram[full_name_col_tg].apply(self.get_first_name).apply(self.normalize_name)
        else:
            df_telegram['norm_first'] = df_telegram[first_name_col_tg].apply(self.normalize_name)

        df_members['norm_full'] = df_members[full_name_col_mem].apply(self.normalize_name)
        df_members['norm_first'] = df_members[full_name_col_mem].apply(self.get_first_name).apply(self.normalize_name)

        # For hver rad i df_members, finn best match
        for idx, row in df_members.iterrows():
            mem_full = row['norm_full']
            mem_first = row['norm_first']

            # Først, sjekk fullnavn matches
            candidates_full = df_telegram[df_telegram['norm_full'].apply(
                lambda tg: difflib.SequenceMatcher(None, tg, mem_full).ratio() >= similarity_threshold
            )]

            if not candidates_full.empty:
                # Velg den med høyest score
                best_idx = candidates_full.apply(
                    lambda r: difflib.SequenceMatcher(None, r['norm_full'], mem_full).ratio(), axis=1
                ).idxmax()
                df_result.at[idx, 'telegram_userid'] = df_telegram.at[best_idx, userid_col]
                df_result.at[idx, 'Match_Type'] = 'Full'
                continue

            # Hvis ingen full match, sjekk fornavn
            candidates_first = df_telegram[df_telegram['norm_first'].apply(
                lambda tg: difflib.SequenceMatcher(None, tg, mem_first).ratio() >= similarity_threshold
            )]

            if not candidates_first.empty:
                # Velg den med høyest score
                best_idx = candidates_first.apply(
                    lambda r: difflib.SequenceMatcher(None, r['norm_first'], mem_first).ratio(), axis=1
                ).idxmax()
                df_result.at[idx, 'telegram_userid'] = df_telegram.at[best_idx, userid_col]
                df_result.at[idx, 'Match_Type'] = 'First'

        # Fjern midlertidige kolonner
        df_telegram.drop(['norm_full', 'norm_first'], axis=1, inplace=True)
        df_members.drop(['norm_full', 'norm_first'], axis=1, inplace=True)

        return df_result

    def _ensure_fieldnames(self,df):
        new_cols = []
        for col in df.columns:
            new_cols.append(col.lower().replace(' ', '_').replace(".","_").strip())
        df.columns = new_cols

    # def read_all_xlsx(self,path : str):
    #     all = []
    #     for file in Path(path).rglob(".xlsx"):
    #         df_single = pd.read_excel(file,engine="openpyxl")
    #         all.append(df_single)
    #     df = pd.concat(all)
    #     self._ensure_fieldnames(df)
    #     df.loc[(df["alder"]<16),"rolle"] = "genf"
    #     df.loc[(df["alder"] <= 18), "rolle"] = "mentor"
    #     df.loc[(df["alder"] > 18), "rolle"] = "mentor"
    #     return df





if __name__ == '__main__':
    genf = GENF()
    # Lagre resultatet i en variabel og print det
    user_dataframe = genf.get_users(which_group='mentor')
    print(user_dataframe)
    
    
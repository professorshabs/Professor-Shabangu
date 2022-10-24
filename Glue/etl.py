import psycopg2
import sys
import boto3
import os
import re
import pandas as pd
import datetime
import io



ENDPOINT = "mycluster.cluster-123456789012.us-east-1.rds.amazonaws.com"
PORT = "5432"
USER = "postgres"
REGION = "af-south-1"
DBNAME = "mydb"
PSWORD = "5Y67bg#r#"

global AWS_ACCESS_KEY
global AWS_SECRET_KEY
global AWS_REGION_NAME
global s3bucketName

AWS_ACCESS_KEY = sys.argv[1]
AWS_SECRET_KEY = sys.argv[2]

AWS_REGION_NAME = sys.argv[3]
s3bucketName = sys.argv[4]



class BankTime(object):
    def __init__(self, bankname):
        self.Bank_name = bankname
    def get_name_year_month(self):
        """
        Return Name year and month
        :return: str str str
        """
        dt = datetime.datetime.now()
        bank = self.Bank_name
        year = dt.year
        month = dt.month
        today = datetime.date.today()
        return bank, year, month, today

class AWSS3(object):

    """Helper class to which add functionality on top of boto3"""

    def __init__(self, bucket=s3bucketName, **kwargs):
        self.BucketName = bucket
        self.client = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION_NAME,
        )

    def put_files(self, Response=None, Key=None):
        """
        Put the File on S3

        """
        try:

            with io.StringIO() as csv_buffer:
                Response.to_csv(csv_buffer, index=False) #dataframe to csv

                response =  self.client.put_object(
                    ACL="private", Bucket=self.BucketName, Key=Key, Body=csv_buffer.getvalue()
                )
            return f"File Save in {Key}"
        except Exception as e:
            print("Error : {} ".format(e))
            return "error"

    def item_exists(self, Key):
        """Given key check if the items exists on AWS S3 :return: Bool"""
        try:
            response_new = self.client.get_object(Bucket=self.BucketName, Key=str(Key))
            return True
        except Exception as e:
            return False

    def get_item(self, Key):

        """Gets the Bytes Data from AWS S3"""

        try:
            response_new = self.client.get_object(Bucket=self.BucketName, Key=str(Key))
            return response_new["Body"].read()
        except Exception as e:
            return False

    def find_one_update(self, data=None, key=None):

        """
        This checks if Key is on S3 if it is return the data from s3
        else store on s3 and return it
        """

        flag = self.item_exists(Key=key)

        if flag:
            data = self.get_item(Key=key)
            return data

        else:
            self.put_files(Key=key, Response=data)
            return data

    def delete_object(self, Key):

        response = self.client.delete_object(Bucket=self.BucketName, Key=Key,)
        return response



class Datalake(AWSS3):
    def __init__(self, base_folder):
        self.base_folder = base_folder
        AWSS3.__init__(self)

    def upload_data_lake(self, csv_data, bank="", year="", month=""):

        if bank != "" and year != "" and month != "":

            """base_folder/bank/YYYY/MM"""

            file_name = "{}_{}.csv".format(
                bank, datetime.date.today().__str__()
            )

            path = "{}/bank={}/year={}/month={}/{}".format(
                self.base_folder,
                bank, year, month, file_name
            )

            self.put_files(Response=csv_data, Key=path)

        else:

            bank, year, month, today = BankTime(bankname=bank).get_name_year_month()

            """base_folder/bank/YYYY/MM"""

            file_name = "{}_{}.csv".format(
                bank, today.__str__()
            )

            path = "{}/bank={}/year={}/month={}/{}".format(
                self.base_folder,
                bank, year, month, file_name
            )

            self.put_files(Response=csv_data, Key=path)

        return True


def main():
    ## get the whole whole
    try:
        conn = psycopg2.connect(host=ENDPOINT, port=PORT, database=DBNAME, user=USER, password=PSWORD)
        sql = """SELECT b.Name bank_name, br.Address,w.Name emp_name, w.Surname emp_surname, w.Position
                , c.Name client_name, c.Surname client_surname,Balance,open_date, Amount, loan_date
                FROM staging.Branch br
                JOIN staging.Bank ON br.Bank_idBank =b.idBank
                JOIN staging.Worker w ON w.Branch_idBranch = br.idBranch
                JOIN staging.Client c ON c.Branch_idBranch = br.idBranch
                JOIN staging.Account a ON a.Client_idClient = c.idClient
                JOIN staging.Loans l ON l.Account_idAccount = a.idAccount """
        data_df = pd.sql.read_sql(sql, conn)  ## We can use pyspark if the table is too big
        print(data_df.head(2))
        conn.close()

        ## It could be easier to do the moving averages in SQL wit window functions

    except Exception as e:
        print("Database connection failed due to {}".format(e))
    data_df = pd.read_csv('output.csv')
    for bank in data_df.bank_name.unique():
        df = data_df.loc[data_df['bank_name'] == bank]
        df['SMA_3Months'] = df['Close'].rolling(90).mean()  ## 3 Months moving average
        print(bank)
        lake_instance = Datalake(base_folder="Data") # loading data to Data/bank/year/month
        lake_instance.upload_data_lake(bank = bank, csv_data=df)


if __name__ == "__main__":
    main()

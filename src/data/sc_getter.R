library(rscorecard)
library(dotenv)
library(dplyr)
library(arrow)

# Set working directory
setwd("C:/Users/svens/Documents/UTSC_Website")

# Load API Key
load_dot_env()
sc_key(Sys.getenv("SC_KEY"))

# Declare which vars we want from the Scorecard
sc_vars <- c("main", "instnm", "control", "credlev",
             "ugds", "cipcode", "cipdesc",
             "earn_count_wne_4yr", "earn_mdn_4yr",
             "ccugprof", "npt4_pub", "npt4_priv")

# Request data and add useful columns
ut_df <- sc_init() %>%
  sc_filter(stabbr == "UT", control != 3, credlev == 3) %>%
  sc_select_(sc_vars) %>%
  sc_year("latest") %>%
  sc_get() %>%
  mutate(cipfield = substr(cipcode, 1, 2)) %>% # Create cipfield column
  filter(ccugprof != 11) %>% # Drops Western Governors University
  mutate(net_price = coalesce(npt4_pub, npt4_priv)) %>% # Create net_price column
  select(-npt4_pub, -npt4_priv) # Drop npt4_pub and npt4_priv columns



# Calculate the average earnings by major across all schools
major_earnings <- ut_df %>%
  filter(complete.cases(.)) %>% # Drop rows with NA values
  group_by(cipcode) %>%
  summarise(tot_mdn_earn_4yr = matrixStats::weightedMedian(earn_mdn_4yr, earn_count_wne_4yr)) 

# Add the total median earnings to the main dataframe
ut_df <- ut_df %>%
  left_join(major_earnings, by = "cipcode")

write_feather(ut_df, "data/ut_data.feather")
write_csv_arrow(ut_df, "data/ut_data.csv")
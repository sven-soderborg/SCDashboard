library(ggplot2)
library(ggimage)
library(dplyr)
library(arrow)

setwd("C:/Users/svens/repos/SCDashboard/src/data/")

# Read in data and add image urls
df <- read_feather("ut_data.feather") %>%
  filter(complete.cases(.)) %>%
  mutate(image = paste0("https://raw.githubusercontent.com/sven-soderborg/SCDashboard/main/src/logos/", instnm, ".png")) %>%
  select(-tot_mdn_earn_4yr, -cipcode, -cipdesc) # Drop tot_mdn_earn_4yr column

df$image <- gsub(" ", "-", df$image)


# Find the average earnings by field across all schools
fields_df <- df %>%
  group_by(cipfield) %>%
  mutate(tot_mdn_earn_4yr =
           as.integer(
             matrixStats::weightedMedian(earn_mdn_4yr, earn_count_wne_4yr)
           )) %>%
  ungroup()

# Find the average earnings by field within each school
sch_field_earnings <- fields_df %>%
  group_by(instnm, cipfield) %>%
  summarise(sch_mdn_earn_4yr =
              as.integer(
                matrixStats::weightedMedian(earn_mdn_4yr, earn_count_wne_4yr)
              ),
            net_price = first(net_price),
            field_desc = first(field_desc),
            image = first(image),
            tot_mdn_earn_4yr = first(tot_mdn_earn_4yr)) %>%
  filter(cipfield %in%
           c("11", "14", "52", "45", "09", "13", "42", "50", "19"))


# Create field labels
plot_labels <- sch_field_earnings %>%
  group_by(cipfield) %>%
  summarise(field_desc = first(field_desc),
            tot_mdn_earn_4yr = first(tot_mdn_earn_4yr)) %>%
  arrange(desc(tot_mdn_earn_4yr))
plot_labels$y <- c(29000, 29000, 29000, 29000, 29000, 29000, 29000, 29000, 29000)

# Axis ticks
custom_ticks <- c(30000, 35000, 40000, 45000, 50000, 55000, 60000, 65000, 70000, 75000, 80000, 85000, 90000, 95000, 100000, 105000, 110000)
top_y_ticks <- c(30000, 40000, 50000, 60000, 70000, 80000, 90000, 100000, 110000)

# Fields over $60,000
top_fields <- sch_field_earnings %>%
  filter(tot_mdn_earn_4yr > 60000) %>%
  arrange(desc(tot_mdn_earn_4yr))

top_labels <- plot_labels %>%
  filter(tot_mdn_earn_4yr > 60000) %>%
  arrange(desc(tot_mdn_earn_4yr))

# Fields under $60,000
bottom_fields <- sch_field_earnings %>%
  filter(tot_mdn_earn_4yr <= 60000) %>%
  arrange(desc(tot_mdn_earn_4yr))

bottom_labels <- plot_labels %>%
  filter(tot_mdn_earn_4yr <= 60000) %>%
  arrange(desc(tot_mdn_earn_4yr))

# Custom theme 
custom_theme <- 
    theme(plot.title = element_text(size = 24, face = "bold", hjust = 0.5),
          plot.subtitle = element_text(size = 18, hjust = 0.5),
          plot.caption = element_text(size = 10),
          axis.text = element_text(size = 12),
          axis.ticks = element_line(size = 0.5),
          axis.ticks.length = unit(0.1, "cm"),
          axis.ticks.margin = unit(0.1, "cm"),
          axis.title.x = element_text(size = 18, margin = margin(t = 10, r = 0, b = 0, l = 0)),
          axis.title.y = element_text(size = 18, margin = margin(t = 0, r = 10, b = 0, l = 0)))

# Plot the top fields 
p <- ggplot(top_fields,
            aes(x = tot_mdn_earn_4yr, y = sch_mdn_earn_4yr)) +
  geom_image(aes(image = image), size = 0.04) +
  geom_label(data = top_labels, aes(label = stringr::str_wrap(field_desc, 10), x = tot_mdn_earn_4yr, y = y)) +
  scale_x_continuous(labels = scales::dollar_format(), limits = c(60000, 93000), breaks = custom_ticks) +
  scale_y_continuous(labels = scales::dollar_format(), breaks = top_y_ticks) +
  labs(title = "Higher Earnings Unveiled:",
       subtitle = "Exploring median earnings for selected fields of study within each university",
       caption = "Source: College Scorecard",
       x = "Median Earnings Across All Universities",
       y = "Median Earning Within Each University") +
  theme_minimal() +
  custom_theme

ggsave("../plots/top_fields_scatterplot.png", p, width = 15, height = 10, units = "in", bg="white")


# Plot the bottom fields
p <- ggplot(bottom_fields,
            aes(x = tot_mdn_earn_4yr, y = sch_mdn_earn_4yr)) +
  geom_image(aes(image = image), size = 0.04) +
  geom_label(data = bottom_labels, aes(label = stringr::str_wrap(field_desc, 10), x = tot_mdn_earn_4yr, y = y)) +
  scale_x_continuous(labels = scales::dollar_format(), limits = c(29000, 55000), breaks = custom_ticks) +
  scale_y_continuous(labels = scales::dollar_format(), limits = c(29000, 55000), breaks = custom_ticks) +
  labs(title = "Lower Earnings Unveiled:",
       subtitle = "Exploring median earnings for selected fields of study within each university",
       caption = "Source: College Scorecard",
       x = "Median Earnings Across All Universities",
       y = "Median Earning Within Each University") +
  theme_minimal() +
  custom_theme

ggsave("../plots/bottom_fields_scatterplot.png", p, width = 15, height = 10, units = "in", bg="white")
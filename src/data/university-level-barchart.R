library(arrow)
library(dplyr)
library(ggplot2)
library(tidyr)

df <- read_feather("../data/ut_data.feather") %>%
  filter(complete.cases(.))

grouped <- df %>%
  group_by(instnm) %>%
  summarise(
    earn_mdn_4yr = matrixStats::weightedMedian(earn_mdn_4yr, earn_count_wne_4yr),
    net_price = mean(net_price)) %>%
  arrange(desc(earn_mdn_4yr))

univ_earn <- grouped %>%
  mutate(instnm = reorder(instnm, earn_mdn_4yr))

univ_earn_long <- univ_earn %>%
  pivot_longer(cols = c(earn_mdn_4yr, net_price),
               names_to = "metric",
               values_to = "value")

# Plot
p <- ggplot(univ_earn_long, aes(x = instnm, y = value, fill = metric)) +
  geom_bar(stat = "identity", position = position_dodge(width = 0.7), width = 0.7) +
  geom_text(aes(label = scales::dollar_format(scale = 1)(round(value))), 
            position = position_dodge(width = 0.7), 
            hjust = -0.3, 
            vjust = 0.5) +
  coord_flip() +
  labs(title = "4-Year Earnings and Net Price of Attendance by University", 
       x = "University", y = "US Dollars", fill = "Legend") +
  scale_fill_manual(
    values = c("earn_mdn_4yr" = "#38a14d", "net_price" = "#FF6347"),
    labels = c("4 Year Median Earnings", "Net Price of Attendance")) +
  scale_y_continuous(labels = scales::label_dollar()) +
  theme_minimal() +
  theme(
    plot.title = element_text(size = 24, face = "bold", hjust=.5),              
    axis.title.x = element_text(size = 16, face = "bold"),
    axis.title.y = element_text(size = 16, face = "bold"),
    axis.text.x = element_text(size = 14),
    axis.text.y = element_text(size = 14),
    legend.title = element_text(size = 16),
    legend.text = element_text(size = 14),
    legend.position = "bottom",
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank()
  ) +
  expand_limits(y = c(NA, max(univ_earn_long$value) * 1.1)) # Increase the x-axis limits (for a flipped plot)

p
ggsave("C:/Users/svens/My Drive/MSES/univ-barchart.png", dpi=300, width=12, height = 8)
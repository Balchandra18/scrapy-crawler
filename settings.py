BOT_NAME = 'scrapy_aks_crawler'

SPIDER_MODULES = ['scrapy_aks_crawler.spiders']
NEWSPIDER_MODULE = 'scrapy_aks_crawler.spiders'

ROBOTSTXT_OBEY = True

ITEM_PIPELINES = {
    'scrapy_aks_crawler.pipelines.AzureBlobPipeline': 300,
}

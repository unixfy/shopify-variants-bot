from discord.ext import commands
from urllib.parse import urlparse
import validators
import discord
import requests
import json
from datetime import datetime
import cloudscraper


TOKEN = "***REMOVED***"
bot = commands.Bot(command_prefix='$')


def generate_error(error):
    error_embed_raw = {
        "title": "An error occurred.",
        "description": "Please check your input, or follow the instructions in the error.",
        "color": 16711684,
        "timestamp": datetime.now().isoformat(),
        "thumbnail": {
            "url": "https://share.unixfy.net/direct/t3xg3dat.png"
        },
        "footer": {
            "icon_url": "https://software.unixfy.net/wp-content/uploads/2020/09/cropped-Blue-ProfilePic-192x192.png",
            "text": "Unixfy Software Development"
        },
        "fields": [
            {
                "name": "Error details",
                "value": error
            }
        ]
    }
    error_embed = discord.Embed.from_dict(error_embed_raw)
    return error_embed


@bot.check
async def globally_block_dms(ctx):
    return ctx.guild is not None

@bot.check
async def whitelist_server_check(ctx):
    # Validate if the guild id is in the whitelist file
    with open("whitelist.txt", "r") as whitelist_file:
        whitelist = whitelist_file.read()
        if str(ctx.guild.id) in whitelist:
            return True
        else:
            return False
            await ctx.send(embed=generate_error(f"**This server `{ctx.guild.id}` does not have an active license!** \n Please contact Unixfy to activate this server."))

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')


@bot.command(name="variants", help="Grabs the variants from a Shopify product you specify.")
@commands.cooldown(1, 5, commands.BucketType.guild)
async def variants(ctx, arg):
    # Check if the argument provided by user is a url
    urlvalidate = validators.url(arg)

    if urlvalidate:
        # Parse the URL into the domain and some components, we will use this later
        domain = urlparse(arg).netloc
        components = urlparse(arg).path.split('/')

        # Block request if "products" isn't the first component of the URL,
        # or if the component after /products/ doesn't exist,
        # because all Shopify URLs have a format like abc.myshopify.com/products/xyz
        try:
            if "products" not in components or not components[-1]:
                await ctx.send(embed=generate_error(f"This URL, `{arg}`, doesn't look like a Shopify product URL."))
                return
        except IndexError:
            await ctx.send(embed=generate_error(f"This URL, `{arg}`, doesn't look like a Shopify URL."))
            return

        # Load Shopify site's product.json file
        try:
            r = cloudscraper.create_scraper()
            print(f'https://{domain}/products/{components[-1]}.json')
            productjson_raw = r.get(f'https://{domain}/products/{components[-1]}.json',
                                           timeout=10)
            print(productjson_raw.text)
            if productjson_raw.status_code == 404:
                await ctx.send(embed=generate_error(
                    "It seems like the product does not exist in this Shopify store\'s API. This probably means the product does not exist!"))
                return

            products = json.loads(productjson_raw.text)["product"]
        except Exception as e:
            await ctx.send(embed=generate_error(
                f"I couldn't retrieve the products.json API for the site `{domain}`. Are you sure this is a Shopify site?"))
            return

        # Only match the desired product (based on the URL supplied by the user)
        if products["handle"] == components[-1]:
            # Set product name & desc & id for later use
            product_name = products["title"]
            product_description = products["body_html"]
            product_id = products["id"]

            # Populate a variable which basically stringifies and formats the variants from Shopify's API
            variants_ids_list = []
            variants_names_list = []
            for variant in products["variants"]:
                variants_ids_list.append(f'{variant["id"]} \n')
                variants_names_list.append(f'{variant["title"]} \n')

            variants_ids = ''.join(variants_ids_list)
            variants_names = ''.join(variants_names_list)

            # Generate embed
            embed_raw = {
                "title": f'Product Name: {product_name}',
                "description": f'ID: {product_id}',
                "color": 4886754,
                "timestamp": datetime.now().isoformat(),
                "thumbnail": {
                    "url": "https://share.unixfy.net/direct/kish0961.png"
                },
                "footer": {
                    "icon_url": "https://software.unixfy.net/wp-content/uploads/2020/09/cropped-Blue-ProfilePic-192x192.png",
                    "text": "Unixfy Software Development"
                },
                "fields": [
                    {
                        "name": "Variant ID",
                        "value": variants_ids,
                        "inline": True
                    },
                    {
                        "name": "Variant Name",
                        "value": variants_names,
                        "inline": True
                    }
                ]
            }

            embed = discord.Embed.from_dict(embed_raw)
            await ctx.send(embed=embed)

    else:
        await ctx.send(embed=generate_error(f"The input you provided, `{arg}`, isn't a valid URL!"))


@bot.event
async def on_command_error(ctx, error):
    print(error)
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(embed=generate_error("You didn't pass enough arguments. You need to specify a Shopify URL."))
    if isinstance(error, commands.errors.CommandInvokeError):
        await ctx.send(embed=generate_error(
            f"An unknown error occurred. More details: ```{error}```.\n \n **Please report this to Unixfy!**"))
    if isinstance(error, commands.errors.CommandOnCooldown):
        await ctx.send(embed=generate_error(
            f"This command is on cooldown. You need to wait {error.retry_after} seconds, then try again! \n Cooldowns are necessary to prevent abuse/blocking."))


bot.run(TOKEN)

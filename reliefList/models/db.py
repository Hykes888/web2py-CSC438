# -*- coding: utf-8 -*-
from gluon.tools import Auth, Service
from gluon.contrib.appconfig import AppConfig

PRODUCTCATEGORY = ('Electronics','Computers', 'Offics Supplies', 'Office Furniture', 'Furniture','Home','Bedding & Bath', 'Lawn & Garden', 'Kitchen & Dining', 'Tools', 'Toys')
STATES = ('AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY','GU','PR','VI')

myconf = AppConfig(reload=True)
db = DAL('sqlite://storage.sqlite')
auth = Auth(db)
auth.settings.allow_basic_login = True
auth.define_tables(username=True)
auth.settings.login_next = URL('default','home')

Product = db.define_table(
    'productInfo',
    Field('productName',label="Product Name",requires=IS_NOT_EMPTY()),
    Field('productDescription','text',label="Product Description",requires=IS_NOT_EMPTY()),
    Field('productCategory',label="Category",requires=IS_NOT_EMPTY()),
    Field('picture','upload' ,label="Upload Image",requires=IS_NOT_EMPTY(),readable=False),
    Field('thumbnail',"upload",label="View Details"),
    Field('comment','text',label="Comments on image",requires=IS_NOT_EMPTY()),
    Field('needsDelivery','boolean',default=False),
    Field('deliveryAmount'),
    Field('estDeliveryAmount',label='Est. Amount'),
    Field('delivered','boolean',default=False),
    auth.signature)

db.productInfo.productCategory.requires = IS_IN_SET(PRODUCTCATEGORY)

db.define_table(
    'productLocation',
    Field('localProductId','reference productInfo',readable=False,writable=False),
    Field('localName',label="Name",requires=IS_NOT_EMPTY(error_message="Please enter name?")),
    Field('localAddress1',label="Product Address",requires=IS_NOT_EMPTY(error_message="Please enter address?")),
    Field('localState', label="Product State",requires=IS_NOT_EMPTY(error_message="Please select a list?")),
    Field('localCity', label="Product City",requires=IS_NOT_EMPTY(error_message="Please enter city?")),
    Field('localZipCode', label='Product Zip Code',requires=IS_NOT_EMPTY(error_message="Please enter zip code?")),
    Field('localPhone', label='Phone Number',requires=IS_NOT_EMPTY(error_message="Please enter phone number?")),
    Field('localEmail', label='Email',requires=IS_NOT_EMPTY(error_message="Please enter email?")),
    auth.signature)

db.productLocation.localEmail.requires = IS_EMAIL(error_message="Where is the @ sign?")
db.productLocation.localPhone.requires = IS_MATCH('^1?((-)\d{3}-?|\(\d{3}\))\d{3}-?\d{4}$', error_message='Please Enter Phone Ex: 1-xxx-xxx-xxxx')
db.productLocation.localZipCode.requires =  IS_MATCH('^\d{5}(-\d{4})?$',error_message='Enter a zip code')
db.productLocation.localState.requires = IS_IN_SET(STATES)

db.define_table(
    'productDest',
    Field('destProductId','reference productInfo',readable=False,writable=False),
    Field('destName',label='Name',requires=IS_NOT_EMPTY()),
    Field('destAddress1',label="Address",requires=IS_NOT_EMPTY()),
    Field('destState', label="State",requires=IS_NOT_EMPTY()),
    Field('destCity', label="City",requires=IS_NOT_EMPTY()),
    Field('destZipCode', label="Zip Code",requires=IS_NOT_EMPTY()),
    Field('destPhone', label="Number",requires=IS_NOT_EMPTY()),
    Field('destEmail', label="Email",requires=IS_NOT_EMPTY()),
    auth.signature)

db.productDest.destZipCode.requires = IS_MATCH('^\d{5}(-\d{4})?$',error_message='Enter a zip code')
db.productDest.destPhone.requires = IS_MATCH('^1?((-)\d{3}-?|\(\d{3}\))\d{3}-?\d{4}$', error_message='Please Enter Phone Ex: 1-xxx-xxx-xxxx')
db.productDest.destEmail.requires = IS_EMAIL(error_message="Where is the @ sign?")
db.productDest.destState.requires = IS_IN_SET(STATES)

db.define_table(
    'productParcel',
    Field('parcelProductId','reference productInfo',readable=False,writable=False),
    Field('productLength','integer',label="Product Length(Unit: Inch)",requires=IS_INT_IN_RANGE(0, 30,error_message="Tim")),
    Field('productWidth','integer',label="Product Width(Unit: Inch)",requires=IS_INT_IN_RANGE(0, 30)),
    Field('productHeight','integer',label="Product Height(Unit: Inch)",requires=IS_INT_IN_RANGE(0, 30)),
    Field('productWeight','integer',label="Product Weight(Unit: lb)",requires=IS_INT_IN_RANGE(0, 30)),
    auth.signature)

db.productParcel.productLength.requires = IS_NOT_EMPTY()
db.productParcel.productWidth.requires = IS_NOT_EMPTY()
db.productParcel.productHeight.requires = IS_NOT_EMPTY()
db.productParcel.productWeight.requires = IS_NOT_EMPTY()

from smarthumb import SMARTHUMB
box = (200,200)
Product.thumbnail.compute = lambda row: SMARTHUMB(row.picture,box)

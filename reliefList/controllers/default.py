# -*- coding: utf-8 -*-
import shippo
import stripe

SORTBY = ('Product Name','Product Description','Product Category')
def index():
    auth.settings.login_next = URL('default','home')
    return dict(form=auth())

def register():
    auth.settings.register_next = URL('defualt', args='index')
    return dict(form=auth.register())

def home():
    return dict()

def deliveryDetails():
    #API into google wallet of paypal
    formProductDelivery = SQLFORM.grid()
    return dict()

def productInput():
    formInput = SQLFORM(db.productInfo,fields=['productName','productDescription','productCategory','picture','comment'])
    if formInput.process().accepted:
        response.flash = 'Now please enter the location of the product?'
        session.productID = formInput.vars.id
        redirect(URL('productLocalAddress'))
    elif formInput.errors:
        response.flash = 'Please Enter all Information'
    return dict(formInput=formInput)

def productLocalAddress():
    localAddressForm = SQLFORM(db.productLocation)
    if localAddressForm.process().accepted:
        response.flash = 'Now please enter the parcel infomation of the product?'
        db(db.productLocation.id == localAddressForm.vars.id).update(**{'localProductId':session.productID})
        redirect(URL('productParcelInfo'))
    elif localAddressForm.errors:
        response.flash = 'Please Enter all Information'
    return dict(localAddressForm=localAddressForm)

def productParcelInfo():
    formParcel = SQLFORM(db.productParcel)
    if formParcel.process().accepted:
        response.flash = 'Product Information is uploaded'
        db(db.productParcel.id == formParcel.vars.id).update(**{'parcelProductId':session.productID})
        redirect(URL('home'))
    elif formParcel.errors:
        response.flash = 'Please Enter all Information'
    return dict(formParcel=formParcel)

def productSearch():
    db.productInfo.thumbnail.represent = lambda value, row: A(IMG(_src=URL('download',args=value)),_href=URL('productDetails',args=row.id))
    formProductInfo = SQLFORM.grid(db.productInfo.needsDelivery == False,
                        create=False,
                        deletable=False,
                        editable=False,
                        csv=False,
                        links_in_grid=False,
                        details=False,
                        fields=[db.productInfo.thumbnail, db.productInfo.productName, db.productInfo.productDescription, db.productInfo.productCategory])
    return dict(formProductInfo=formProductInfo)

def productDetails():
    id = request.args(0)
    row = db.productInfo(id)
    return dict(row=row)

def productPurchase():
    prodId = request.args(0)
    formDest = SQLFORM(db.productDest)
    if formDest.process().accepted:
        response.flash = 'Destnation information saved.'
        db(db.productInfo.id == prodId).update(**{'needsDelivery':'True'})
        db(db.productDest.id == formDest.vars.id).update(**{'destProductId':prodId})
        session.shippo_data=dict(prodId=prodId)
        redirect(URL('productDeliveryPayment'))
    elif formDest.errors:
        response.flash = 'form has errors'
    return dict(formDest=formDest,prodId=prodId)

def productDeliveryPayment():
    prodId = session.shippo_data['prodId']
    address_fromQ = db(db.productLocation.localProductId == prodId).select()
    address_toQ = db(db.productDest.destProductId == prodId).select()
    parcelsQ = db(db.productParcel.parcelProductId == prodId).select()
    for af in address_fromQ:
        address_from = {'name':af.localName,'street1':af.localAddress1,'city':af.localCity,'state':af.localState,'zip':af.localZipCode,'country':'US','phone':af.localPhone,'email':af.localEmail}
    for at in address_toQ:
        address_to = {'name':at.destName,'street1':at.destAddress1,'city':at.destCity,'state':at.destState,'zip':at.destZipCode,'country':'US','phone':at.destPhone,'email':at.destEmail}
    for p in parcelsQ:
        parcel = {'length':p.productLength,'width':p.productWidth,'height':p.productHeight,'distance_unit':'in','weight':p.productWeight,'mass_unit':'lb'}
    shippo.api_key = "shippo_test_81e32315bb414f66cf221381bc13faf9f2577125"
    shipmentInfo = shippo.Shipment.create(
        address_from = address_from,
        address_to = address_to,
        parcels = [parcel],
        async = False
        )
    db(db.productInfo.id == prodId).update(**{'estDeliveryAmount':min(float(rate['amount_local']) for rate in shipmentInfo.rates)})
    return dict()

def deliveryDonationSearch():
    db.productInfo.thumbnail.represent = lambda value, row: A(IMG(_src=URL('download',args=value)),_href=URL('paymentDetails',args=row.id))
#     query = ((db.productInfo.needsDelivery == True)& (db.akb_doccenter.category == db.akb_doccenter_category.uuid))
    formDonation = SQLFORM.grid(((db.productInfo.needsDelivery == True)&(db.productInfo.delivered == False)),
                    create=False,
                    deletable=False,
                    editable=False,
                    csv=False,
                    links_in_grid=False,
                    details=False,
                    fields=[db.productInfo.thumbnail,db.productInfo.productName,db.productInfo.productDescription,db.productInfo.productCategory,db.productInfo.estDeliveryAmount])
    return dict(formDonation=formDonation)

def paymentDetails():
    prodId = request.args(0)
    session.productIdStripe = dict(prodId=prodId)
    address_fromQ = db(db.productLocation.localProductId == prodId).select()
    address_toQ = db(db.productDest.destProductId == prodId).select()
    parcelsQ = db(db.productParcel.parcelProductId == prodId).select()
    for af in address_fromQ:
        address_from = {'name':af.localName,'street1':af.localAddress1,'city':af.localCity,'state':af.localState,'zip':af.localZipCode,'country':'US','phone':af.localPhone,'email':af.localEmail}
    for at in address_toQ:
        address_to = {'name':at.destName,'street1':at.destAddress1,'city':at.destCity,'state':at.destState,'zip':at.destZipCode,'country':'US','phone':at.destPhone,'email':at.destEmail}
    for p in parcelsQ:
        parcel = {'length':p.productLength,'width':p.productWidth,'height':p.productHeight,'distance_unit':'in','weight':p.productWeight,'mass_unit':'lb'}
    shippo.api_key = "shippo_test_81e32315bb414f66cf221381bc13faf9f2577125"
    shipmentInfo = shippo.Shipment.create(
        address_from = address_from,
        address_to = address_to,
        parcels = [parcel],
        async = False
        )
    lowestRate=min(float(rate['amount_local']) for rate in shipmentInfo.rates)
    dollars, cents = str(lowestRate).split(".")
    amount = dollars + cents
    return dict(product=prodId,amount=amount,lowestRate=lowestRate,PK_TOKEN='pk_test_6pRNASCoBOKtIshFeQd4XMUh')

def paymentCharge():
    prodId = session.productIdStripe['prodId']
    stripe.api_key = "sk_test_BQokikJOvBiI2HlWgH4olfQ2"
    # Token is created using Checkout or Elements!
    # Get the payment token ID submitted by the form:
    token = request.vars.stripeToken
    amount = int(request.vars.amount)
    # Charge the user's card:
    charge = stripe.Charge.create(
        amount=amount,
        currency="usd",
        description="Example charge",
        source=token,
    )
    db(db.productInfo.id == prodId).update(**{'delivered':'True'})

#    db.payment.insert(invoice_id=invoice_id,
#                      amount_due = amount,
#                      amount_paid = amount if charge.paid else 0,
#                      stripe_charge_id = charge.id,
                      # error_message = charge.message
#    )
    if charge.paid:
        return 'customer paid'
    else:
        return 'invalid charge - not paid'

def user():
    form = auth.login().process(next=URL('home'))
    return dict(form=auth())

@cache.action()
def download():
    return response.download(request, db)

def call():
    return service()

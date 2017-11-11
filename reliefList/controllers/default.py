# -*- coding: utf-8 -*-
import shippo
import stripe


def index():
    auth.settings.login_next = URL('default','home')
    return dict(form=auth())

def register():
    auth.settings.register_next = URL('defualt', args='index')
    return dict(form=auth.register())

@auth.requires_login()
def home():
    return dict()

@auth.requires_login()
def deliveryDetails():
    #API into google wallet of paypal
    formProductDelivery = SQLFORM.grid()
    return dict()

@auth.requires_login()
def productInput():
    formInput = SQLFORM(db.productInfo,submit_button='Next',formstyle='table2cols',fields=['productName','productDescription','productCategory','picture','comment'])
    formInput.add_button('Previous', URL('home'))
    if formInput.process().accepted:
        response.flash = 'Now please enter the location of the product?'
        session.productID = formInput.vars.id
        redirect(URL('productLocalAddress'))
    elif formInput.errors:
        response.flash = 'Please Enter all Information'
    return dict(formInput=formInput)

@auth.requires_login()
def productLocalAddress():
    localAddressForm = SQLFORM(db.productLocation,submit_button='Next',formstyle='table2cols')
    localAddressForm.add_button('Previous', URL('home'))
    if localAddressForm.process(keepvalues=True).accepted:
        shippo.api_key = "shippo_test_81e32315bb414f66cf221381bc13faf9f2577125"
        address_validation = shippo.Address.create(
            name = localAddressForm.vars.localName,
            company = "heicheleList",
            street1 = localAddressForm.vars.localAddress1,
            city = localAddressForm.vars.localCity,
            state = localAddressForm.vars.localState,
            zip = localAddressForm.vars.localZipCode,
            country = "US",
            email = localAddressForm.vars.localEmail,
            validate = True
            )
        if address_validation['validation_results']['is_valid'] == True:
            response.flash = 'Now please enter the parcel infomation of the product?'
            db(db.productLocation.id == localAddressForm.vars.id).update(**{'localProductId':session.productID})
            session.localAddress = ""
            redirect(URL('productParcelInfo'))
        else:
            session.localAddress ="Not a valid US shipping address, please enter a shipable address."
            response.flash = 'Address is not a valid US address.'
            redirect(URL('productLocalAddress'))
    elif localAddressForm.errors:
        response.flash = 'Please Enter all Information'
    return dict(localAddressForm=localAddressForm,valid=session.localAddress)

@auth.requires_login()
def productParcelInfo():
    formParcel = SQLFORM(db.productParcel)
    if formParcel.process().accepted:
        response.flash = 'Product Information is uploaded'
        db(db.productParcel.id == formParcel.vars.id).update(**{'parcelProductId':session.productID})
        redirect(URL('home'))
    elif formParcel.errors:
        response.flash = 'Please Enter all Information'
    return dict(formParcel=formParcel)

@auth.requires_login()
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

@auth.requires_login()
def productDetails():
    id = request.args(0)
    row = db.productInfo(id)
    return dict(row=row)

@auth.requires_login()
def productPurchase():
    prodId = request.args(0)
    formDest = SQLFORM(db.productDest,submit_button='Next',formstyle='table2cols')
    formDest.add_button('Previous', URL('home'))
    if formDest.process(keepvalues=True).accepted:
        shippo.api_key = "shippo_test_81e32315bb414f66cf221381bc13faf9f2577125"
        address_validation = shippo.Address.create(
            name = formDest.vars.destName,
            company = "heicheleList",
            street1 = formDest.vars.destAddress1,
            city = formDest.vars.destCity,
            state = formDest.vars.destState,
            zip = formDest.vars.destZipCode,
            country = "US",
            email = formDest.vars.destEmail,
            validate = True
            )
        if address_validation['validation_results']['is_valid'] == True:
            response.flash = 'Destnation information saved.'
            formDest.process().accepted
            db(db.productInfo.id == prodId).update(**{'needsDelivery':'True'})
            db(db.productDest.id == formDest.vars.id).update(**{'destProductId':prodId})
            session.destAddress = ""
            session.shippo_data=dict(prodId=prodId)
            redirect(URL('productDeliveryPayment'))
        else:
            session.destAddress ="This is not a valid US shipping address, please enter a shipable address."
            response.flash = 'Address is not a valid US address.'
            redirect(URL('productPurchase'))
    elif formDest.errors:
        response.flash = 'form has errors'
    return dict(formDest=formDest,valid=session.destAddress)

@auth.requires_login()
def productDeliveryPayment():
    prodId = session.shippo_data['prodId']
    address_fromQ = db(db.productLocation.localProductId == prodId).select()
    address_toQ = db(db.productDest.destProductId == prodId).select()
    parcelsQ = db(db.productParcel.parcelProductId == prodId).select()
    for af in address_fromQ:
        address_from_Input = {'name':af.localName,'street1':af.localAddress1,'city':af.localCity,'state':af.localState,'zip':af.localZipCode,'country':'US','phone':af.localPhone,'email':af.localEmail}
    for at in address_toQ:
        address_to_Input = {'name':at.destName,'street1':at.destAddress1,'city':at.destCity,'state':at.destState,'zip':at.destZipCode,'country':'US','phone':at.destPhone,'email':at.destEmail}
    for p in parcelsQ:
        parcel_Input = {'length':p.productLength,'width':p.productWidth,'height':p.productHeight,'distance_unit':'in','weight':p.productWeight,'mass_unit':'lb'}
    shippo.api_key = "shippo_test_81e32315bb414f66cf221381bc13faf9f2577125"
    shipmentInfo = shippo.Shipment.create(
        address_from = address_from_Input,
        address_to = address_to_Input,
        parcels = [parcel_Input],
        async = False
        )
    db(db.productInfo.id == prodId).update(**{'estDeliveryAmount':min(float(rate['amount_local']) for rate in shipmentInfo.rates)})
    return dict()

@auth.requires_login()
def deliveryDonationSearch():
    db.productInfo.thumbnail.represent = lambda value, row: A(IMG(_src=URL('download',args=value)),_href=URL('deliveryChoice',args=row.id))
    formDonation = SQLFORM.grid(((db.productInfo.needsDelivery == True)&(db.productInfo.delivered == False)),
                    create=False,
                    deletable=False,
                    editable=False,
                    csv=False,
                    links_in_grid=False,
                    details=False,
                    fields=[db.productInfo.thumbnail,db.productInfo.productName,db.productInfo.productDescription,db.productInfo.productCategory,db.productInfo.estDeliveryAmount])
    return dict(formDonation=formDonation)

@auth.requires_login()
def deliveryChoice():
    prodId = request.args(0)
    address_fromQ = db(db.productLocation.localProductId == prodId).select()
    address_toQ = db(db.productDest.destProductId == prodId).select()
    parcelsQ = db(db.productParcel.parcelProductId == prodId).select()
    for af in address_fromQ:
        address_from_I = {'name':af.localName,'street1':af.localAddress1,'city':af.localCity,'state':af.localState,'zip':af.localZipCode,'country':'US','phone':af.localPhone,'email':af.localEmail}
    for at in address_toQ:
        address_to_I = {'name':at.destName,'street1':at.destAddress1,'city':at.destCity,'state':at.destState,'zip':at.destZipCode,'country':'US','phone':at.destPhone,'email':at.destEmail}
    for p in parcelsQ:
        parcel = {'length':p.productLength,'width':p.productWidth,'height':p.productHeight,'distance_unit':'in','weight':p.productWeight,'mass_unit':'lb'}
    shippo.api_key = "shippo_test_81e32315bb414f66cf221381bc13faf9f2577125"
    shipmentInfo = shippo.Shipment.create(
        address_from = address_from_I,
        address_to = address_to_I,
        parcels = [parcel],
        async = False
        )
    #store shipmentInfo
    rate_dict={}
    for postRate in shipmentInfo.rates:
        rate_dict[postRate['object_id']] = postRate['amount_local']
    session.productIdStripe_data = dict(id=prodId,sI=rate_dict)
    return dict(shipmentInfo=shipmentInfo)

@auth.requires_login()
def paymentDetails():
    rateId = request.args(0)
    prodId = session.productIdStripe_data['id']
    rateData= session.productIdStripe_data['sI'][rateId]
    dollars, cents = str(rateData).split(".")
    amount = dollars + cents
    return dict(amount=amount,price=rateData,PK_TOKEN='pk_test_6pRNASCoBOKtIshFeQd4XMUh')

@auth.requires_login()
def paymentCharge():
    prodId = session.productIdStripe_data['id']
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
        return dict(paid='customer paid')
    else:
        return dict(paid='invalid charge - not paid')


def user():
    form = auth.login().process(next=URL('home'))
    return dict(form=auth())

@cache.action()
def download():
    return response.download(request, db)

def call():
    return service()

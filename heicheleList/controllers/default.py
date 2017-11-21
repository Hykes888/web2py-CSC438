# -*- coding: utf-8 -*-
#-------------------------------------------------------------#
#  Application: heicheleList                                  #
#  Developer: Tim Heichele                                    #
#-------------------------------------------------------------#
import shippo
import stripe
from gluon.contrib.appconfig import AppConfig
#from gluon.tools import Mail
#mail = Mail()
#mail.settings.server = 'smtp.gmail.com:587'
#mail.settings.sender = 'heicheleList@gmail.com'
#mail.settings.login = 'heicheleList:'
#mail.settings.tls=True

#-------------------------------------------------------------#
#  Function: index                                            #
#  Purpase: Is the default page for heicheleList              #
#-------------------------------------------------------------#
def index():
    auth.settings.login_next = URL('default','home')
    return dict(form=auth())

#-------------------------------------------------------------#
#  Function: register                                         #
#  Purpase: Is the sign up page and function using internal   #
#           Web2py functionality for sign up                  #
#-------------------------------------------------------------#
def register():
    auth.settings.register_next = URL('defualt', args='index')
    return dict(form=auth.register())

#-------------------------------------------------------------#
#  Function: home                                             #
#  Purpase: This is a placeholder if the home page would ever #
#           need functionality from the model or API but the  #
#           home page is the main navigation of heicheleList  #
#  Security: User must be logged in                           #
#-------------------------------------------------------------#
@auth.requires_login()
def home():
    return dict()

#-------------------------------------------------------------#
#  Function: productInput                                     #
#  Purpose: processes the input for a new product and stores  #
#           in a productInfo table and validates the data     #
#           entered. Stores all information in a session      #
#  DB table: productInfo                                      #
#  Security: User must be logged in                           #
#-------------------------------------------------------------#
@auth.requires_login()
def productInput():
    formInput = SQLFORM(db.productInfo,submit_button='Next',formstyle='table2cols',fields=['productName','productDescription','productCategory','picture','comment'])
    formInput.add_button('Previous', URL('home'))
    if formInput.validate():
        response.flash = 'Now please enter the location of the product?'
        session.formInput = formInput.vars
        redirect(URL('productLocalAddress'))
    elif formInput.errors:
        response.flash = 'Please Enter all Information'
    return dict(formInput=formInput)

#-------------------------------------------------------------#
#  Function: productLocalAddress                              #
#  Purpose: Processes the input of the current location of a  #
#           product being donated. It validates that the      #
#           address is a valid shipable US address. And also  #
#           validates user input. Storeas all information in  #
#           a session.                                        #
#  DB table: productLocation                                  #
#  Security: User must be logged in                           #
#  API: shippo                                                #
#-------------------------------------------------------------#
@auth.requires_login()
def productLocalAddress():
    localAddressForm = SQLFORM(db.productLocation,submit_button='Next',formstyle='table2cols')
    localAddressForm.add_button('Previous', URL('home'))
    if localAddressForm.validate():
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
            session.localAddress = ""
            session.localAddressForm = localAddressForm.vars
            redirect(URL('productParcelInfo'))
        elif address_validation['validation_results']['is_valid'] == False:
            session.localAddress ="Not a valid US shipping address, please enter a shipable address."
            response.flash = 'Address is not a valid US address.'
            redirect(URL('productLocalAddress'))
    elif localAddressForm.errors:
        response.flash = 'Please Enter all Information'
    return dict(localAddressForm=localAddressForm,valid=session.localAddress)

#-------------------------------------------------------------#
#  Function: productParcelInfo                                #
#  Purpose: Processes the input of the size of the product    #
#           donated. Validates user inputs for parcels and    #
#           stores the information of the entire entry of a   #
#           product.                                          #
#  DB table: productParcelInfo                                #
#  Security: User must be logged in                           #
#-------------------------------------------------------------#
@auth.requires_login()
def productParcelInfo():
    formParcel = SQLFORM(db.productParcel)
    if formParcel.validate():
        response.flash = 'Product Information is uploaded'
        productid = db.productInfo.insert(**{'productName':session.formInput.productName,
                                             'productDescription':session.formInput.productDescription,
                                             'productCategory':session.formInput.productCategory,
                                             'picture':session.formInput.picture,
                                             'comment':session.formInput.comment})
        db.productLocation.insert(**{'localProductId':productid,
                                     'localName':session.localAddressForm.localName,
                                     'localAddress1':session.localAddressForm.localAddress1,
                                     'localState':session.localAddressForm.localState,
                                     'localCity':session.localAddressForm.localCity,
                                     'localZipCode':session.localAddressForm.localZipCode,
                                     'localPhone':session.localAddressForm.localPhone,
                                     'localEmail':session.localAddressForm.localEmail})
        db.productParcel.insert(**{'parcelProductId':productid,
                                   'productLength':formParcel.vars.productLength,
                                   'productWidth':formParcel.vars.productHeight,
                                   'productHeight':formParcel.vars.productHeight,
                                   'productWeight':formParcel.vars.productWeight})
        db.commit()
        redirect(URL('home'))
    elif formParcel.errors:
        response.flash = 'Please Enter all Information'
    return dict(formParcel=formParcel)

#-------------------------------------------------------------#
#  Function: productSearch                                    #
#  Purpose: Provides a grid of all products avaliabe in the   #
#           productInfo table. Makes the IMG the link to the  #
#           productsDetials page.                             #
#  DB table: productInfo                                      #
#  Security: User must be logged in                           #
#-------------------------------------------------------------#
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

#-------------------------------------------------------------#
#  Function: productDetails                                   #
#  Purpose: Provides a detail of a the selected product from  #
#           product search page                               #
#  DB table: productInfo                                      #
#  Security: User must be logged in                           #
#-------------------------------------------------------------#
@auth.requires_login()
def productDetails():
    id = request.args(0)
    row = db.productInfo(id)
    return dict(row=row)

#-------------------------------------------------------------#
#  Function: productPurchase                                  #
#  Purpose: Logic to the first stage of getting the product   #
#           delivered to the person in need. The function     #
#           interacts with shippo to volidate the shipping    #
#           destination is a USA address. We also udate the   #
#           tables to make sure the product can't be choosen  #
#           again. It also validates the inputs.              #
#  DB table: productInfo, productDest                         #
#  API: Shippo                                                #
#  Security: User must be logged in                           #
#-------------------------------------------------------------#
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
            db.orderHistory.insert(orderHistoryID=prodId,inNeedUser=auth.user_id)
            session.destAddress = ""
            session.shippo_data=dict(prodId=prodId)
            redirect(URL('productDeliveryPayment'))
        else:
            session.destAddress ="This is not a valid US shipping address, please enter a shipable address."
            response.flash = 'Address is not a valid US address.'
            redirect(URL('productPurchase',args=prodId))
    elif formDest.errors:
        response.flash = 'form has errors'
    return dict(formDest=formDest,valid=session.destAddress)

#-------------------------------------------------------------#
#  Function: productDeliveryPayment                           #
#  Purpose: Logic does an estimate with the source address    #
#           and the destination address and update the        #
#           database with the estimated amount.               #
#  DB table: productInfo, productDest, productLocation,       #
#            productParcel                                    #
#  API: Shippo                                                #
#  Security: User must be logged in                           #
#-------------------------------------------------------------#
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

#-------------------------------------------------------------#
#  Function: productDonationSearch                            #
#  Purpose: Logic does a query that provides all the avilable #
#           donations that are avaliable to pay for delivery  #
#  DB table: productInfo                                      #
#  Security: User must be logged in                           #
#-------------------------------------------------------------#
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

#-------------------------------------------------------------#
#  Function: deliveryChoice                                   #
#  Purpose: Logic finds all the shipping parcel prices from   #
#           USPS and allos the user to select the delivery    #
#           donation he wants.                                #
#  DB table: productInfo, productDest, productLocation,       #
#            productParcel                                    #
#  API: Shippo                                                #
#  Security: User must be logged in                           #
#-------------------------------------------------------------#
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
    rate_dict={}
    postService_dict={}
    for postRate in shipmentInfo.rates:
        rate_dict[postRate['object_id']] = postRate['amount_local']
        postService_dict[postRate['object_id']] = postRate['provider']
    session.productIdStripe_data = dict(id=prodId,sI=rate_dict, psI=postService_dict)
    return dict(shipmentInfo=shipmentInfo)

#-------------------------------------------------------------#
#  Function: paymentDetails                                   #
#  Purpose: Logic takes the object_id from shippo to get the  #
#           cost of the delivery choice and then stores the   #
#           information in the datebase including the tracking#
#           number and package sticker in a pdf.              #
#  DB table: deliveryHistory,                                 #
#  API: Shippo                                                #
#  Security: User must be logged in                           #
#-------------------------------------------------------------#
@auth.requires_login()
def paymentDetails():
    rateId = request.args(0)
    prodId = session.productIdStripe_data['id']
    rateData= session.productIdStripe_data['sI'][rateId]
    postService = session.productIdStripe_data['psI'][rateId]
    dollars, cents = str(rateData).split(".")
    amount = dollars + cents
    transaction = shippo.Transaction.create(
        rate=rateId,
        label_file_type="PDF",
        async=False )
    if transaction.status == "SUCCESS":
        shippingLabelURL = transaction.label_url
        trackingNum = transaction.tracking_number
    else:
        errorMessage = transaction.messages
    db.deliveryHistory.insert(delieveryId=prodId,
                            deliveryCost=rateData,
                            deliveryPostSel=postService,
                            deliveryTrackNum=trackingNum,
                            deliveryShipMentInfo=shippingLabelURL)
    #Email to product owner with shipping sticker and tracking URL, Plus email the person in need with the tracking number
    return dict(amount=amount,price=rateData,PK_TOKEN='pk_test_6pRNASCoBOKtIshFeQd4XMUh')

#-------------------------------------------------------------#
#  Function: paymentCharge                                    #
#  Purpose: Logic takes the delivery amount and charges the   #
#           credit card at stripe and updates database about  #
#           the productInfo.                                  #
#  DB table: productInfo, payment                             #
#  API: Stripe                                                #
#  Security: User must be logged in                           #
#-------------------------------------------------------------#
@auth.requires_login()
def paymentCharge():
    prodId = session.productIdStripe_data['id']
    stripe.api_key = "sk_test_BQokikJOvBiI2HlWgH4olfQ2"
    token = request.vars.stripeToken
    amount = int(request.vars.amount)
    charge = stripe.Charge.create(
        amount=amount,
        currency="usd",
        description="Example charge",
        source=token,
    )
    db(db.productInfo.id == prodId).update(**{'delivered':'True'})
    db.payment.insert(paymentId=prodId,
                    amount_paid = amount,
                    stripeId = charge.id
                    )
    #Email to with recept for future versions.
    if charge.paid:
        return dict(paid='customer paid')
    else:
        return dict(paid='invalid charge - not paid')

#-------------------------------------------------------------#
#  Function: myHeicheleList                                   #
#  Purpose: Logic is a placeholder for future but is          #
#           navigation for user history on heicheleList       #
#  Security: User must be logged in                           #
#-------------------------------------------------------------#
@auth.requires_login()
def myHeicheleList():
    return dict()

#-------------------------------------------------------------#
#  Function: myProductDonation                                #
#  Purpose: Provides forms for donated product for the user.  #
#           One form allows you to click and edit a product   #
#           that was donated. And the other form is about     #
#           past donated products that have been delivered    #
#  DB table: productInfo,                                     #
#  Security: User must be logged in                           #
#-------------------------------------------------------------#
@auth.requires_login()
def myProductDonation():
    db.productInfo.thumbnail.represent = lambda value, row: A(IMG(_src=URL('download',args=value)),_href=URL('productEdit',args=row.id))
    formProductDonated = SQLFORM.grid(((db.productInfo.delivered==False) & (db.productInfo.created_by==auth.user_id)),
                    create=False,
                    deletable=True,
                    editable=False,
                    csv=False,
                    links_in_grid=False,
                    details=False,
                    fields=[db.productInfo.thumbnail,db.productInfo.productName,db.productInfo.productDescription,db.productInfo.productCategory])
    db.productInfo.thumbnail.represent = lambda value, row: IMG(_src=URL('download',args=value))
    formProductDel = SQLFORM.grid(((db.productInfo.delivered==True) & (db.productInfo.created_by==auth.user_id)),
                    create=False,
                    deletable=False,
                    editable=False,
                    csv=False,
                    links_in_grid=False,
                    details=False,
                    fields=[db.productInfo.thumbnail,db.productInfo.productName,db.productInfo.productDescription,db.productInfo.productCategory])
    return dict(formProductDonated=formProductDonated,formProductDel=formProductDel)

#-------------------------------------------------------------#
#  Function: productEdit                                      #
#  Purpose: Provides a form to edit product that was donated  #
#           but has not been delivered.                       #
#  DB table: productInfo                                      #
#  Security: User must be logged in                           #
#-------------------------------------------------------------#
@auth.requires_login()
def productEdit():
    id = request.args(0)
    record = db.productInfo(id)
    formUpdate = SQLFORM(db.productInfo,record,submit_button='Update',formstyle='table2cols',fields=['productName','productDescription','productCategory','picture','comment'],showid=False)
    if formUpdate.process().accepted:
       response.flash = 'form accepted'
    elif formUpdate.errors:
       response.flash = 'form has errors'
    return dict(formUpdate=formUpdate, record=record)

#-------------------------------------------------------------#
#  Function: myDeliveryDonation                               #
#  Purpose: Form that provides history of paid donation for   #
#           delivery of products.                             #
#  DB table: deliveryHistory                                  #
#  Security: User must be logged in                           #
#-------------------------------------------------------------#
@auth.requires_login()
def myDeliveryDonation():
    db.productInfo.thumbnail.represent = lambda value, row: IMG(_src=URL('download',args=value))
    formDelDonation = SQLFORM.grid(((db.deliveryHistory.delieveryId == db.productInfo.id) & (db.deliveryHistory.created_by == auth.user_id)),
                    create=False,
                    deletable=False,
                    editable=False,
                    csv=False,
                    links_in_grid=False,
                    details=False,
                    fields=[db.productInfo.thumbnail,db.productInfo.productName,db.deliveryHistory.deliveryCost,db.deliveryHistory.deliveryPostSel]
                    )
    return dict(formDelDonation=formDelDonation)

#-------------------------------------------------------------#
#  Function: myProductOrders                                  #
#  Purpose: Provides a form for past orders or product that   #
#           were ordered.                                     #
#  DB table: productInfo                                      #
#  Security: User must be logged in                           #
#-------------------------------------------------------------#
@auth.requires_login()
def myProductOrders():
    db.productInfo.thumbnail.represent = lambda value, row: IMG(_src=URL('download',args=value))
    formOrderHistory = SQLFORM.grid(((db.orderHistory.orderHistoryID == db.productInfo.id) & (db.orderHistory.inNeedUser == auth.user_id)),
                    create=False,
                    deletable=False,
                    editable=False,
                    csv=False,
                    links_in_grid=False,
                    details=False,
                    fields=[db.productInfo.thumbnail,db.productInfo.productName,db.productInfo.productDescription,db.productInfo.productCategory]
                    )
    return dict(formOrderHistory=formOrderHistory)

def user():
    form = auth.login().process(next=URL('home'))
    return dict(form=auth())

@auth.requires_login()
@cache.action()
def download():
    return response.download(request, db)

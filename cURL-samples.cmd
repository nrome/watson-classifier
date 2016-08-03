Dialog - Get list of dialogs
curl -k -u "4062825e-09e8-4fef-9f2d-e40af0d6cff9":"836d1SaFEooX" "https://watson-api-explorer.mybluemix.net/dialog/api/v1/dialogs"

Dialog - Get profile variables
curl -k -u "4062825e-09e8-4fef-9f2d-e40af0d6cff9":"836d1SaFEooX" "https://watson-api-explorer.mybluemix.net/dialog/api/v1/dialogs/06217458-eda6-4601-8a59-af3a955a1dfe/profile?client_id=611841"

Dialog - Set profile variables
curl -k -X PUT -H "content-type: application/json" -H "accept: application/json" -d "{'client_id': 611841,'name_values': [{'name': 'Product_Name','value': 'Puddy'}, {'name': 'Doog','value': 'Pritters'}]}" -u "4062825e-09e8-4fef-9f2d-e40af0d6cff9":"836d1SaFEooX" "https://watson-api-explorer.mybluemix.net/dialog/api/v1/dialogs/06217458-eda6-4601-8a59-af3a955a1dfe/profile"
curl -k -X PUT -H "content-type: application/json" -H "accept: application/json" -d "{'client_id':611841,'name_values':[{'name':'Product_Name','value': 'PRODUCT_NAME'},{'name':'Doog','value':'THE_DOOG'}]}" -u "4062825e-09e8-4fef-9f2d-e40af0d6cff9":"836d1SaFEooX" "https://watson-api-explorer.mybluemix.net/dialog/api/v1/dialogs/06217458-eda6-4601-8a59-af3a955a1dfe/profile"

Q-and-A/service/ - POST
curl -X POST -H "Content-Type:application/json" -d "{\"question\":\"Can I get a degree in HCA?\", \"client_id\":\"156008\", \"conversation_id\":\"164662\"}" "http://localhost:5000/service/"

R-and-R - Create SOLR cluster
curl -k -X POST -u "5945d177-c161-4022-a85c-e0ec35cad099":"L57wQZDI8fnE" "https://gateway.watsonplatform.net/retrieve-and-rank/api/v1/solr_clusters" -d "" 

R-and-R - Check status of SOLR cluster
curl -k -u "5945d177-c161-4022-a85c-e0ec35cad099":"L57wQZDI8fnE" "https://gateway.watsonplatform.net/retrieve-and-rank/api/v1/solr_clusters/sce5690497_52a7_46f0_b6a2_1341c7c2b63e"

R-and-R - Upload sample SOLR config file
curl -k -X POST -H "Content-Type: application/zip" -u "5945d177-c161-4022-a85c-e0ec35cad099":"L57wQZDI8fnE" "https://gateway.watsonplatform.net/retrieve-and-rank/api/v1/solr_clusters/sce5690497_52a7_46f0_b6a2_1341c7c2b63e/config/tivoli-config" --data-binary @tivoli_solr_config.zip

R-and-R - Create collection 'tivoli-collection'
curl -k -X POST -u "5945d177-c161-4022-a85c-e0ec35cad099":"L57wQZDI8fnE" "https://gateway.watsonplatform.net/retrieve-and-rank/api/v1/solr_clusters/sce5690497_52a7_46f0_b6a2_1341c7c2b63e/solr/admin/collections" -d "action=CREATE&name=tivoli-collection&collection.configName=tivoli-config"

R-and-R Add documents
curl -k -X POST -H "Content-Type: application/json" -u "5945d177-c161-4022-a85c-e0ec35cad099":"L57wQZDI8fnE" "https://gateway.watsonplatform.net/retrieve-and-rank/api/v1/solr_clusters/sce5690497_52a7_46f0_b6a2_1341c7c2b63e/solr/tivoli-collection/update" --data-binary @tivoli_data_full.json

R-and-R Delete SOLR cluster
curl -k -X DELETE -u "5945d177-c161-4022-a85c-e0ec35cad099":"L57wQZDI8fnE" "https://gateway.watsonplatform.net/retrieve-and-rank/api/v1/solr_clusters/sce5690497_52a7_46f0_b6a2_1341c7c2b63e"

R-and-R Delete Ranker
curl -k -X DELETE -u "5945d177-c161-4022-a85c-e0ec35cad099":"L57wQZDI8fnE" "https://gateway.watsonplatform.net/retrieve-and-rank/api/v1/rankers/42B250x11-rank-323"

R-and-R Python script to create Ranker
c:\python27\python train_mine.py -u 5945d177-c161-4022-a85c-e0ec35cad099:L57wQZDI8fnE -i tivoli_gt.csv -c sce5690497_52a7_46f0_b6a2_1341c7c2b63e -x tivoli-collection -n "tivoli-ranker"

R-and-R Retrieve status of ranker
curl -k -u "5945d177-c161-4022-a85c-e0ec35cad099":"L57wQZDI8fnE"  "https://gateway.watsonplatform.net/retrieve-and-rank/api/v1/rankers/42B250x11-rank-328"

R-and-R Retrieve search results
https://5945d177-c161-4022-a85c-e0ec35cad099:L57wQZDI8fnE@gateway.watsonplatform.net/retrieve-and-rank/api/v1/solr_clusters/sce5690497_52a7_46f0_b6a2_1341c7c2b63e/solr/tivoli-collection/select?q=what is the basic mechanism of the transonic aileron buzz&wt=json&fl=id,title

R-and-R Retrieve reranked results
https://5945d177-c161-4022-a85c-e0ec35cad099:L57wQZDI8fnE@gateway.watsonplatform.net/retrieve-and-rank/api/v1/solr_clusters/sce5690497_52a7_46f0_b6a2_1341c7c2b63e/solr/tivoli-collection/fcselect?ranker_id=42AF7Ex10-rank-319&q=prepare&nbsp;me&nbsp;for&nbsp;management&wt=json&fl=id,program,description
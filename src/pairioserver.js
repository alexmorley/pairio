const express = require('express');
const cors = require('cors');
const MongoClient = require('mongodb').MongoClient;
const sign_pair = require(__dirname+'/sign_pair.js').sign_pair;

let test_signature='test_signature'; ////// REMOVE THIS AFTER TESTING
let user_tokens={
  'jmagland@flatironinstitute.org':'test_token',
  'magland':'test_token'
};

async function main() {
  let DB=new PairioDB();
  try {
    await DB.connect('mongodb://localhost:27017','pairio');
  }
  catch(err) {
    console.error(err);
    console.error('Error connecting to database: '+err.message);
    process.exit(-1);
  }
  let API=new PairioApi(DB);
  let SERVER=new PairioServer(API);
  try {
    await start_http_server(SERVER.app());
  }
  catch(err) {
    console.error(err);
    console.error('Error starting server: '+err.message);
    process.exit(-1);
  }
}
main();

function PairioDB() {
  let m_collection=null;
  this.connect=async function(url,db_name) {
    let client=await MongoClient.connect(url,{ useNewUrlParser: true });
    let db=client.db(db_name);
    m_collection=db.collection("pairs");
  }
  this.find=async function(key) {
    if (!m_collection) {
      return 'Not connected to database';
    }
    let cursor=m_collection.find({key:key});
    return await cursor.toArray();
  }
  this.set=async function(key,value,user) {
    if (!m_collection) {
      return 'Not connected to database';
    }
    m_collection.updateOne({key:key,user:user},{$set:{value: value}},{upsert:true});
  }
}

function PairioApi(DB) {
  this.get=async function(key) {
    let docs=await DB.find(key);
    return {
      success:true,
      documents:docs
    };
  };

  this.set=async function(key,value,user,signature) {
    let ok=await verify_signature(key,value,user,signature);
    if (!ok) {
      return {success:false,error:'Invalid signature'};
    }
    await DB.set(key,value,user);
    return {success:true};
  };
  async function verify_signature(key,value,user,signature) {
    if (test_signature) {
      if (signature==test_signature) return true;
    }
    if (!(user in user_tokens)) return false;
    let token=user_tokens[user];
    let sig=sign_pair(key,value,token);
    return (signature==sig);
  }
}

function PairioServer(API) {
  this.app = function() {
    return m_app;
  };

  let m_app = express();
  m_app.set('json spaces', 4); // when we respond with json, this is how it will be formatted
  m_app.use(cors());

  m_app.use(express.json());

  // API get
  m_app.get('/get/:key', async function(req, res) {
    let params = req.params;
    try {
      obj = await API.get(params.key);
    }
    catch(err) {
      console.error(err);
      res.json({
        success:false,
        error:err.message
      });
      return;
    }
    res.json(obj);
  });

  // API get
  m_app.get('/set/:key/:value', async function(req, res) {
    let params = req.params;
    let query = req.query;
    if (!query.user) {
      res.json({
        success:false,
        error:'Missing query parameter: user'
      });
      return;
    }
    if (!query.signature) {
      res.json({
        success:false,
        error:'Missing query parameter: signature'
      });
      return;
    }
    try {
      obj = await API.set(params.key,params.value,query.user,query.signature);
    }
    catch(err) {
      console.error(err);
      res.json({
        success:false,
        error:err.message
      });
      return;
    }
    res.json(obj);
  });
}

async function start_http_server(app) {
  let listen_port=process.env.PORT||25340;
  app.port=listen_port;
  if (process.env.SSL != null ? process.env.SSL : listen_port % 1000 == 443) {
    // The port number ends with 443, so we are using https
    app.USING_HTTPS = true;
    app.protocol = 'https';
    // Look for the credentials inside the encryption directory
    // You can generate these for free using the tools of letsencrypt.org
    const options = {
      key: fs.readFileSync(__dirname + '/encryption/privkey.pem'),
      cert: fs.readFileSync(__dirname + '/encryption/fullchain.pem'),
      ca: fs.readFileSync(__dirname + '/encryption/chain.pem')
    };

    // Create the https server
    app.server = require('https').createServer(options, app);
  } else {
    app.protocol = 'http';
    // Create the http server and start listening
    app.server = require('http').createServer(app);
  }
  await app.server.listen(listen_port);
  console.info(`Server is running ${app.protocol} on port ${app.port}`);
}
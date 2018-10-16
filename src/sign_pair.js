const crypto = require('crypto'); 

exports.sign_pair=sign_pair;

function sign_pair(key,value,token) {
  let ret=sign_message({
    key:key,
    value:value,
  },token);
  return ret;
}

function sign_message(msg, token) {
  let shasum = crypto.createHash('sha1');
  let obj={
    message:msg,
    token:token
  };
  shasum.update(JSON.stringify(obj));
  return shasum.digest('hex');
  
  /*
  const signer = crypto.createSign('sha256');
  signer.update(JSON.stringify(msg));
  signer.end();

  const signature = signer.sign(private_key);
  const signature_hex = signature.toString('hex');

  return signature_hex;
  */
}

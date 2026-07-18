const express=require("express")
const router=express.Router()
const authGitController=require("../controllers/authGitController");

router.route("/github")
    .get(authGitController.gitAuthorization)


router.route("/github/callback")
    .get(authGitController.gitTempToken)

module.exports=router;
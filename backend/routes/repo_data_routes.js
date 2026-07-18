const express=require("express");
const router=express.Router()
const repo_dataController=require("../controllers/repo_dataController")


router.route("/repos")
    .get(repo_dataController.fetchRepoData)

module.exports=router;
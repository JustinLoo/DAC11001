import argparse
import pcbnew
import sys
import re
from pathlib import Path
def gerberdrillremove(filename,debug=False):
    ms1=r'G04 Created by KiCad \([\s\S]*?\) date [\s\S]*$'
    ms2=r'%TF.CreationDate,\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}-\d{2}:\d{2}\*%'
    ms3=r'%TF.ProjectId,\S+?,[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12},rev\?\*%'
    ms4=r'%TF.GenerationSoftware,[\s\S]*?\*%'
    ms5=r'; DRILL file {[\s\S]*?} date \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}-\d{2}\d{2}\s*'
    ms6=r'; #@! TF.CreationDate,\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}-\d{2}:\d{2}\s*'
    ms7=r'; #@! TF.GenerationSoftware,[\s\S]*$'


    s1=[]
    with open(filename) as f:
        s=f.read()
        for l in s.split('\n'):
            m1=re.match(ms1,l)
            m2=re.match(ms2,l)
            m3=re.match(ms3,l)
            m4=re.match(ms4,l)
            m5=re.match(ms5,l)
            m6=re.match(ms6,l)
            m7=re.match(ms7,l)
            if (m1 is not None) or (m2 is not None) or (m3 is not None) or (m4 is not None) or (m5 is not None) or (m6 is not None) or (m7 is not None):
                if debug:
                    print('removed',l)
                pass
            else:
                s1.append(l)
    with open(filename,'w') as f:
        f.write('\n'.join(s1))
def fab(pcbfile,outputdir,gerber=True,drill=True,bom=True,xypos=True,keepdateveretc=False,debug=False,layers=None):

    b=pcbnew.LoadBoard(pcbfile)
    layerset=b.GetEnabledLayers()
    layerseq=layerset.Seq()
    alllayername=[b.GetLayerName(i) for i in layerset.Seq()]
    psme=['B.Paste', 'F.Paste', 'B.Silkscreen', 'F.Silkscreen', 'B.Mask', 'F.Mask', 'Edge.Cuts']
    culayername=[b.GetLayerName(i) for i in layerset.CuStack()]
    culayerid=layerset.CuStack()
    if debug:
        print(culayerid)
    culayerid_list=list(culayerid)
    toplayerid=culayerid_list[0]
    bottomlayerid=culayerid_list[-1]
    if layers is None:
        layers=[i for i in alllayername if i in psme or i in culayername]
    else:
        layers=layers 

    if gerber:
        if debug:
            print(culayername)
        pctl=pcbnew.PLOT_CONTROLLER(b)
        popt=pctl.GetPlotOptions()
        #popt.SetOutputDirectory('%s/%s'%(Path(pcbfile).parent,outputdir))
        popt.SetOutputDirectory(outputdir)
        popt.SetDrillMarksType(pcbnew.DRILL_MARKS_NO_DRILL_SHAPE)
        #zonefiller=pcbnew.ZONE_FILLER(b)
        #zonefiller.Fill(b.Zones())
        for lname in layers:
            if debug:
                print(lname)
            pctl.SetLayer(b.GetLayerID(lname))
            pctl.OpenPlotfile(lname,pcbnew.PLOT_FORMAT_GERBER)
            pctl.PlotLayer()
            pctl.ClosePlot()
            if not keepdateveretc:
                filename='%s/%s/%s-%s.gbr'%(Path(pcbfile).parent,outputdir,Path(pcbfile).stem,lname.replace('.','_'))
                gerberdrillremove(filename)


                
    if drill:
        drill_writer=pcbnew.EXCELLON_WRITER(b)
        drill_writer.SetOptions(
                aMirror=False,
                aMinimalHeader=False,
                aMerge_PTH_NPTH=False,
                aOffset=pcbnew.VECTOR2I(0, 0)
                )
        drill_writer.SetFormat(False)  # True for Metric format False for Inches
        drill_writer.SetMapFileFormat(pcbnew.PLOT_FORMAT_GERBER)
        drill_writer.CreateDrillandMapFilesSet(
                aPlotDirectory='%s/%s'%(Path(pcbfile).parent,outputdir),
                aGenDrill=True,
                aGenMap=True
                )
        for ext in 'NPTH.drl,NPTH-drl_map.gbr,PTH.drl,PTH-drl_map.gbr'.split(','):
            filename='%s/%s/%s-%s'%(Path(pcbfile).parent,outputdir,Path(pcbfile).stem,ext)
            gerberdrillremove(filename)
            #with open(filename) as f:
            #    s=f.read()
    edgecut=[]
    drawings=[]
    for d in b.GetDrawings():
        if (d.GetLayerName()=="Edge.Cuts"):
            edgecut.append(d)
        else:
            drawings.append(d)

    exs=[]
    eys=[]
    exstart=[e.GetStart().x for e in edgecut]
    exend=[e.GetEnd().x for e in edgecut]
    exs.extend(exstart)
    exs.extend(exend)
    eystart=[e.GetStart().y for e in edgecut]
    eyend=[e.GetEnd().y for e in edgecut]
    eys.extend(eystart)
    eys.extend(eyend)
    #if len(edgecut)==1:
    #    ex=exs[0]
    #    ey=eys[0]
    #else:
    ex=min(exs)
    ey=max(eys)
    if debug:
        print('ex,ey',ex,ey)


    fps=b.GetFootprints()
    bomdict={}
    posF=[]
    posB=[]
    posA=[]
    posDNP=[]
    missingvendor=[]
    debug=False
    for ifp,fp in enumerate(fps):
        layername=fp.GetLayerName()
        layerid=fp.GetLayer()
        pos=fp.GetPosition()
        orideg=fp.GetOrientationDegrees()
        footprint=fp.GetFPIDAsString()
        ref=fp.GetReference()
        value=fp.GetValue()
        if 0:#ref=="C4":
            debug=True
        else:
            debug=False
        if value=='DNP':
            dnpdict=dict(Ref=ref,Val=None,Package=footprint,PosX=None,PosY=None,ROT=None,Side='')
            posDNP.append(dnpdict)
            pass
        elif fp.IsDNP():
            dnpdict=dict(Ref=ref,Val=None,Package=footprint,PosX=None,PosY=None,ROT=None,Side='')
            posDNP.append(dnpdict)
            pass
        else:
            if not fp.IsExcludedFromBOM():
                fieldnames=[fd.GetName() for fd in fp.GetFields()]
                if 'Vendor' in fieldnames:
                    vendor=fp.GetFieldText('Vendor')
                else:
                    missingvendor.append((ref,value))
                    vendor=None
                if debug:
                    print(vendor)
                if (vendor,footprint) not in bomdict:
                    bomdict[(vendor,footprint)]=[]
                bomdict[(vendor,footprint)].append(ref)

                if not fp.IsExcludedFromPosFiles():
                    xrelative='%.06f'%round((pos.x-ex)*1e-6,6)
                    yrelative='%.06f'%round((ey-pos.y)*1e-6,6)
                    orideg6='%.06f'%orideg
                    if layerid==toplayerid:
                        tdict=dict(Ref=ref,Val=vendor,Package=footprint,PosX=xrelative,PosY=yrelative,ROT=orideg6,Side='top')
                        posF.append(tdict)
                        posA.append(tdict)
                    elif layerid==bottomlayerid:
                        bdict=dict(Ref=ref,Val=vendor,Package=footprint,PosX=xrelative,PosY=yrelative,ROT=orideg6,Side='bottom')
                        posB.append(bdict)
                        posA.append(bdict)
                    else:
                        print(toplayerid,bottomlayerid,layerid)
                        exit('part %s  suppose on front or back not %s'%(ref,layername))
                else:
                    dnpdict=dict(Ref=ref,Val=None,Package=footprint,PosX=None,PosY=None,ROT=None,Side='')
                    posDNP.append(dnpdict)
    if len(missingvendor)>0:
        print(missingvendor)
        exit('Error: missing vendor info')
    import csv
    outputdirpath='%s/%s/'%(Path(pcbfile).parent,outputdir)
    if bom:
        ibom=1
        csvlines=[]
        if len(bomdict)>0:
            for (vendor,footprint),ref in bomdict.items():
                csvlines.append(dict(Id=ibom,Designator=';'.join(ref),Footprint=footprint,Quantity=len(ref),Designation=vendor))
                ibom=ibom+1
            with open(outputdirpath+'/bom.csv','w') as csvfile:
                writer=csv.DictWriter(csvfile,fieldnames=list(csvlines[0].keys()),delimiter=',')#,quoting=csv.QUOTE_NONNUMERIC)
                writer.writeheader()
                for l in csvlines:
                    writer.writerow(l)
    if xypos:
        if len(posF)>0:
            with open(outputdirpath+'/pos_top.csv','w') as csvfile:
                writer=csv.DictWriter(csvfile,fieldnames=list(posF[0].keys()),delimiter=',')#,quoting=csv.QUOTE_NONNUMERIC)
                writer.writeheader()
                for l in posF:
                    writer.writerow(l)
        if len(posB)>0:
            with open(outputdirpath+'/pos_bottom.csv','w') as csvfile:
                writer=csv.DictWriter(csvfile,fieldnames=list(posB[0].keys()),delimiter=',')#,quoting=csv.QUOTE_NONNUMERIC)
                writer.writeheader()
                for l in posB:
                    writer.writerow(l)
        if len(posA)>0:
            with open(outputdirpath+'/pos_all.csv','w') as csvfile:
                writer=csv.DictWriter(csvfile,fieldnames=list(posA[0].keys()),delimiter=',')#,quoting=csv.QUOTE_NONNUMERIC)
                writer.writeheader()
                for l in posA:
                    writer.writerow(l)
        if len(posDNP)>0:
            with open(outputdirpath+'/pos_dnp.csv','w') as csvfile:
                writer=csv.DictWriter(csvfile,fieldnames=list(posA[0].keys()),delimiter=',')#,quoting=csv.QUOTE_NONNUMERIC)
                writer.writeheader()
                for l in posDNP:
                    writer.writerow(l)
if __name__=="__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(dest='pcbfile', help='kicad_pcb filename ')
    parser.add_argument(dest='outputdir', help='output directory')
    parser.add_argument('-gerber', dest='gerber',action='store_true',help='generate gerber file')
    parser.add_argument('-drill', dest='drill',action='store_true',help='generate drill file')
    parser.add_argument('-bom', dest='bom',action='store_true',help='generate bom file')
    parser.add_argument('-xypos', dest='xypos',action='store_true',help='generate xypos file')
    parser.add_argument('-keepdateveretc', dest='keepdateveretc',action='store_true',help='keep date, version, generation software etc')
    parser.add_argument('-debug', dest='debug',action='store_true',help='print debug message')
    parser.add_argument('-layers', dest='layers',type=str,help='layers name',default=None,nargs='*')

    clargs = parser.parse_args()
    fab(pcbfile=clargs.pcbfile,outputdir=clargs.outputdir,gerber=clargs.gerber,drill=clargs.drill,bom=clargs.bom,xypos=clargs.xypos,keepdateveretc=clargs.keepdateveretc,debug=clargs.debug,layers=clargs.layers)
